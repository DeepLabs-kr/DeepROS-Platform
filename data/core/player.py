import asyncio
import time
import logging
from typing import Optional, Dict, Any, List, Callable, Generator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..database import SessionLocal
from ..models import ROSMessage, RecordingSession, MessageIndex
from ..config import DataSettings
import gzip
from datetime import datetime


logger = logging.getLogger(__name__)


class ROSPlayer:
    """ROS message player similar to rosbag play functionality."""
    
    def __init__(self, settings: Optional[DataSettings] = None):
        self.settings = settings or DataSettings()
        self.is_playing = False
        self.current_session: Optional[RecordingSession] = None
        self.playback_task: Optional[asyncio.Task] = None
        self.message_callback: Optional[Callable] = None
        self.playback_rate = self.settings.DEFAULT_PLAYBACK_RATE
        self.loop_playback = self.settings.LOOP_PLAYBACK
        self.start_time_offset = self.settings.START_TIME_OFFSET
        
        # Playback state
        self.start_time: Optional[float] = None
        self.current_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_messages = 0
        self.played_messages = 0
    
    async def play_session(
        self,
        session_id: int,
        topics: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        playback_rate: Optional[float] = None,
        loop: Optional[bool] = None,
        message_callback: Optional[Callable] = None
    ) -> bool:
        """Play back a recording session."""
        if self.is_playing:
            raise RuntimeError("Playback is already in progress")
        
        # Load session
        db = SessionLocal()
        try:
            session = db.query(RecordingSession).filter(
                RecordingSession.id == session_id
            ).first()
            
            if not session:
                logger.error(f"Recording session not found: {session_id}")
                return False
            
            self.current_session = session
            
        finally:
            db.close()
        
        # Set playback parameters
        self.playback_rate = playback_rate or self.playback_rate
        self.loop_playback = loop if loop is not None else self.loop_playback
        self.message_callback = message_callback
        
        # Set time range
        self.start_time = start_time or self.current_session.start_time
        self.end_time = end_time or self.current_session.end_time
        self.current_time = self.start_time
        
        # Get total message count
        self.total_messages = await self._get_message_count(topics, self.start_time, self.end_time)
        
        if self.total_messages == 0:
            logger.warning("No messages found for playback")
            return False
        
        # Start playback
        self.is_playing = True
        self.playback_task = asyncio.create_task(
            self._playback_loop(topics, self.start_time, self.end_time)
        )
        
        logger.info(f"Started playback of session: {self.current_session.name}")
        logger.info(f"Messages: {self.total_messages}, Time range: {self.start_time:.2f} - {self.end_time:.2f}")
        
        return True
    
    async def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
        
        self.is_playing = False
        
        if self.playback_task:
            await self.playback_task
        
        logger.info(f"Stopped playback. Played {self.played_messages}/{self.total_messages} messages")
    
    async def pause_playback(self):
        """Pause the current playback."""
        if self.is_playing:
            self.is_playing = False
            logger.info("Playback paused")
    
    async def resume_playback(self):
        """Resume the current playback."""
        if not self.is_playing and self.current_session:
            self.is_playing = True
            self.playback_task = asyncio.create_task(
                self._playback_loop(None, self.current_time, self.end_time)
            )
            logger.info("Playback resumed")
    
    async def _playback_loop(
        self, 
        topics: Optional[List[str]], 
        start_time: float, 
        end_time: float
    ):
        """Main playback loop."""
        try:
            while self.is_playing and self.current_time <= end_time:
                # Get next batch of messages
                messages = await self._get_messages_batch(
                    topics, 
                    self.current_time, 
                    min(self.current_time + 1.0, end_time)  # 1 second batches
                )
                
                if not messages:
                    # No more messages in this time range
                    if self.loop_playback:
                        # Reset to start
                        self.current_time = start_time
                        self.played_messages = 0
                        logger.info("Looping playback - restarting from beginning")
                        continue
                    else:
                        break
                
                # Play messages in chronological order
                for message in messages:
                    if not self.is_playing:
                        break
                    
                    # Calculate delay based on playback rate
                    if self.played_messages > 0:
                        time_diff = message.timestamp - self.current_time
                        delay = time_diff / self.playback_rate
                        
                        if delay > 0:
                            await asyncio.sleep(delay)
                    
                    # Call message callback
                    if self.message_callback:
                        try:
                            await self.message_callback(message)
                        except Exception as e:
                            logger.error(f"Error in message callback: {e}")
                    
                    self.current_time = message.timestamp
                    self.played_messages += 1
                    
                    # Log progress every 1000 messages
                    if self.played_messages % 1000 == 0:
                        progress = (self.played_messages / self.total_messages) * 100
                        logger.info(f"Playback progress: {progress:.1f}% ({self.played_messages}/{self.total_messages})")
            
            logger.info(f"Playback completed. Played {self.played_messages} messages")
            
        except Exception as e:
            logger.error(f"Error in playback loop: {e}")
            self.is_playing = False
    
    async def _get_messages_batch(
        self, 
        topics: Optional[List[str]], 
        start_time: float, 
        end_time: float,
        limit: int = 1000
    ) -> List[ROSMessage]:
        """Get a batch of messages for the given time range."""
        db = SessionLocal()
        try:
            query = db.query(ROSMessage).filter(
                and_(
                    ROSMessage.recording_session_id == self.current_session.id,
                    ROSMessage.timestamp >= start_time,
                    ROSMessage.timestamp <= end_time
                )
            )
            
            if topics:
                query = query.filter(ROSMessage.topic_name.in_(topics))
            
            messages = query.order_by(ROSMessage.timestamp).limit(limit).all()
            
            # Decompress messages if needed
            for message in messages:
                if self._is_compressed(message.data):
                    message.data = gzip.decompress(message.data)
                    message.data_size = len(message.data)
            
            return messages
            
        finally:
            db.close()
    
    async def _get_message_count(
        self, 
        topics: Optional[List[str]], 
        start_time: float, 
        end_time: float
    ) -> int:
        """Get the total number of messages in the time range."""
        db = SessionLocal()
        try:
            query = db.query(ROSMessage).filter(
                and_(
                    ROSMessage.recording_session_id == self.current_session.id,
                    ROSMessage.timestamp >= start_time,
                    ROSMessage.timestamp <= end_time
                )
            )
            
            if topics:
                query = query.filter(ROSMessage.topic_name.in_(topics))
            
            return query.count()
            
        finally:
            db.close()
    
    def _is_compressed(self, data: bytes) -> bool:
        """Check if data is compressed with gzip."""
        return data.startswith(b'\x1f\x8b')
    
    def get_playback_stats(self) -> Dict[str, Any]:
        """Get current playback statistics."""
        if not self.current_session:
            return {}
        
        progress = (self.played_messages / self.total_messages * 100) if self.total_messages > 0 else 0
        
        return {
            'session_id': self.current_session.id,
            'session_name': self.current_session.name,
            'is_playing': self.is_playing,
            'playback_rate': self.playback_rate,
            'current_time': self.current_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_messages': self.total_messages,
            'played_messages': self.played_messages,
            'progress_percent': progress,
            'loop_playback': self.loop_playback
        }
    
    def seek_to_time(self, timestamp: float):
        """Seek to a specific timestamp in the recording."""
        if not self.current_session:
            return False
        
        if timestamp < self.start_time or timestamp > self.end_time:
            logger.warning(f"Timestamp {timestamp} is outside playback range")
            return False
        
        self.current_time = timestamp
        
        # Update played message count (approximate)
        db = SessionLocal()
        try:
            count = db.query(ROSMessage).filter(
                and_(
                    ROSMessage.recording_session_id == self.current_session.id,
                    ROSMessage.timestamp <= timestamp
                )
            ).count()
            self.played_messages = count
        finally:
            db.close()
        
        logger.info(f"Seeked to timestamp: {timestamp}")
        return True
    
    def get_session_info(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a recording session."""
        db = SessionLocal()
        try:
            session = db.query(RecordingSession).filter(
                RecordingSession.id == session_id
            ).first()
            
            if not session:
                return None
            
            # Get topic statistics
            topic_stats = session.get_topic_statistics()
            
            return {
                'id': session.id,
                'name': session.name,
                'description': session.description,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'duration': session.duration,
                'total_messages': session.total_messages,
                'total_size_bytes': session.total_size_bytes,
                'topics_count': session.topics_count,
                'is_active': session.is_active,
                'is_compressed': session.is_compressed,
                'topic_statistics': topic_stats,
                'created_at': session.created_at,
                'updated_at': session.updated_at
            }
            
        finally:
            db.close()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available recording sessions."""
        db = SessionLocal()
        try:
            sessions = db.query(RecordingSession).order_by(
                RecordingSession.created_at.desc()
            ).all()
            
            return [
                {
                    'id': session.id,
                    'name': session.name,
                    'description': session.description,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'duration': session.duration,
                    'total_messages': session.total_messages,
                    'total_size_bytes': session.total_size_bytes,
                    'topics_count': session.topics_count,
                    'is_active': session.is_active,
                    'created_at': session.created_at
                }
                for session in sessions
            ]
            
        finally:
            db.close() 