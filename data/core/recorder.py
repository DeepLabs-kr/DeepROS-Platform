import asyncio
import time
import logging
from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.orm import Session
from ..database import SessionLocal, init_db
from ..models import ROSMessage, RecordingSession, TopicInfo, MessageIndex
from ..config import DataSettings
import json
import gzip
from datetime import datetime


logger = logging.getLogger(__name__)


class ROSRecorder:
    """ROS message recorder similar to rosbag record functionality."""
    
    def __init__(self, settings: Optional[DataSettings] = None):
        self.settings = settings or DataSettings()
        self.current_session: Optional[RecordingSession] = None
        self.is_recording = False
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.settings.BATCH_SIZE)
        self.processing_task: Optional[asyncio.Task] = None
        self.topic_info_cache: Dict[str, TopicInfo] = {}
        self.sequence_counters: Dict[str, int] = {}
        
        # Initialize database
        init_db()
        
        # Load existing topic info
        self._load_topic_info()
    
    def _load_topic_info(self):
        """Load existing topic information from database."""
        db = SessionLocal()
        try:
            topics = db.query(TopicInfo).all()
            for topic in topics:
                self.topic_info_cache[topic.topic_name] = topic
        except Exception as e:
            logger.error(f"Failed to load topic info: {e}")
        finally:
            db.close()
    
    async def start_recording(
        self, 
        session_name: str, 
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> RecordingSession:
        """Start a new recording session."""
        if self.is_recording:
            raise RuntimeError("Recording is already in progress")
        
        db = SessionLocal()
        try:
            # Create new recording session
            self.current_session = RecordingSession(
                name=session_name,
                description=description,
                start_time=time.time(),
                settings_dict=settings or {}
            )
            
            db.add(self.current_session)
            db.commit()
            db.refresh(self.current_session)
            
            self.is_recording = True
            self.processing_task = asyncio.create_task(self._process_message_queue())
            
            logger.info(f"Started recording session: {session_name} (ID: {self.current_session.id})")
            return self.current_session
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def stop_recording(self) -> Optional[RecordingSession]:
        """Stop the current recording session."""
        if not self.is_recording or not self.current_session:
            return None
        
        self.is_recording = False
        
        # Wait for processing task to complete
        if self.processing_task:
            await self.processing_task
        
        # Update session end time and statistics
        db = SessionLocal()
        try:
            session = db.query(RecordingSession).filter(
                RecordingSession.id == self.current_session.id
            ).first()
            
            if session:
                session.end_time = time.time()
                session.duration = session.end_time - session.start_time
                session.is_active = False
                session.update_statistics()
                
                db.commit()
                db.refresh(session)
                
                logger.info(f"Stopped recording session: {session.name} (Duration: {session.duration:.2f}s)")
                return session
                
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            db.rollback()
        finally:
            db.close()
        
        return None
    
    async def record_message(
        self,
        topic_name: str,
        message_type: str,
        data: bytes,
        timestamp: Optional[float] = None,
        source_node: Optional[str] = None,
        destination_node: Optional[str] = None,
        qos_profile: Optional[Dict[str, Any]] = None,
        header_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a ROS message."""
        if not self.is_recording or not self.current_session:
            logger.warning("Cannot record message: no active recording session")
            return False
        
        # Validate message size
        if len(data) > self.settings.MAX_MESSAGE_SIZE_BYTES:
            logger.warning(f"Message too large: {len(data)} bytes (max: {self.settings.MAX_MESSAGE_SIZE_BYTES})")
            return False
        
        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = time.time()
        
        # Update sequence counter
        if topic_name not in self.sequence_counters:
            self.sequence_counters[topic_name] = 0
        self.sequence_counters[topic_name] += 1
        
        # Create message object
        message_data = {
            'topic_name': topic_name,
            'message_type': message_type,
            'data': data,
            'timestamp': timestamp,
            'source_node': source_node,
            'destination_node': destination_node,
            'qos_profile': qos_profile,
            'header_info': header_info,
            'sequence_number': self.sequence_counters[topic_name],
            'recording_session_id': self.current_session.id
        }
        
        # Add to processing queue
        try:
            await asyncio.wait_for(
                self.message_queue.put(message_data), 
                timeout=self.settings.MESSAGE_TIMEOUT_SECONDS
            )
            return True
        except asyncio.TimeoutError:
            logger.error("Message queue timeout")
            return False
    
    async def _process_message_queue(self):
        """Process messages from the queue in batches."""
        batch = []
        
        while self.is_recording or not self.message_queue.empty():
            try:
                # Get message with timeout
                message_data = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                batch.append(message_data)
                
                # Process batch when full or when recording stops
                if (len(batch) >= self.settings.BATCH_SIZE or 
                    (not self.is_recording and self.message_queue.empty())):
                    
                    await self._save_message_batch(batch)
                    batch = []
                    
            except asyncio.TimeoutError:
                # Process remaining batch
                if batch:
                    await self._save_message_batch(batch)
                    batch = []
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
    
    async def _save_message_batch(self, batch: List[Dict[str, Any]]):
        """Save a batch of messages to the database."""
        if not batch:
            return
        
        db = SessionLocal()
        try:
            for message_data in batch:
                # Compress data if enabled
                data = message_data['data']
                is_compressed = False
                
                if self.settings.COMPRESSION_ENABLED:
                    data = gzip.compress(data, compresslevel=self.settings.COMPRESSION_LEVEL)
                    is_compressed = True
                
                # Create ROS message
                message = ROSMessage(
                    topic_name=message_data['topic_name'],
                    message_type=message_data['message_type'],
                    timestamp=message_data['timestamp'],
                    sequence_number=message_data['sequence_number'],
                    data=data,
                    data_size=len(data),
                    recording_session_id=message_data['recording_session_id'],
                    source_node=message_data['source_node'],
                    destination_node=message_data['destination_node'],
                    qos_dict=message_data['qos_profile'],
                    header_dict=message_data['header_info']
                )
                
                db.add(message)
                db.flush()  # Get the message ID
                
                # Create index entry
                index_entry = MessageIndex.from_message(
                    message, 
                    message_data['recording_session_id']
                )
                db.add(index_entry)
                
                # Update topic info
                await self._update_topic_info(message_data)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save message batch: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _update_topic_info(self, message_data: Dict[str, Any]):
        """Update topic information cache and database."""
        topic_name = message_data['topic_name']
        
        if topic_name not in self.topic_info_cache:
            # Create new topic info
            db = SessionLocal()
            try:
                topic_info = TopicInfo(
                    topic_name=topic_name,
                    message_type=message_data['message_type'],
                    is_active=True
                )
                
                db.add(topic_info)
                db.commit()
                db.refresh(topic_info)
                
                self.topic_info_cache[topic_name] = topic_info
                
            except Exception as e:
                logger.error(f"Failed to create topic info: {e}")
                db.rollback()
            finally:
                db.close()
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """Get current recording statistics."""
        if not self.current_session:
            return {}
        
        return {
            'session_id': self.current_session.id,
            'session_name': self.current_session.name,
            'start_time': self.current_session.start_time,
            'duration': time.time() - self.current_session.start_time if self.is_recording else 0,
            'total_messages': self.current_session.total_messages,
            'total_size_bytes': self.current_session.total_size_bytes,
            'topics_count': self.current_session.topics_count,
            'queue_size': self.message_queue.qsize(),
            'is_recording': self.is_recording
        }
    
    def list_sessions(self, active_only: bool = False) -> List[RecordingSession]:
        """List all recording sessions."""
        db = SessionLocal()
        try:
            query = db.query(RecordingSession)
            if active_only:
                query = query.filter(RecordingSession.is_active == True)
            
            return query.order_by(RecordingSession.created_at.desc()).all()
        finally:
            db.close()
    
    def delete_session(self, session_id: int) -> bool:
        """Delete a recording session and all its messages."""
        db = SessionLocal()
        try:
            session = db.query(RecordingSession).filter(
                RecordingSession.id == session_id
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
                logger.info(f"Deleted recording session: {session.name}")
                return True
            else:
                logger.warning(f"Recording session not found: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            db.rollback()
            return False
        finally:
            db.close() 