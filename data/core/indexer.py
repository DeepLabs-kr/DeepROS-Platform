import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..database import SessionLocal
from ..models import MessageIndex, ROSMessage, TopicInfo
from ..config import DataSettings
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class MessageIndexer:
    """Message indexing and search functionality."""
    
    def __init__(self, settings: Optional[DataSettings] = None):
        self.settings = settings or DataSettings()
        self.indexing_task: Optional[asyncio.Task] = None
        self.is_indexing = False
    
    async def start_auto_indexing(self):
        """Start automatic indexing of messages."""
        if self.is_indexing:
            return
        
        self.is_indexing = True
        self.indexing_task = asyncio.create_task(self._auto_index_loop())
        logger.info("Started automatic message indexing")
    
    async def stop_auto_indexing(self):
        """Stop automatic indexing."""
        if not self.is_indexing:
            return
        
        self.is_indexing = False
        if self.indexing_task:
            await self.indexing_task
        
        logger.info("Stopped automatic message indexing")
    
    async def _auto_index_loop(self):
        """Automatic indexing loop."""
        while self.is_indexing:
            try:
                await self.rebuild_index()
                await asyncio.sleep(self.settings.INDEX_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Error in auto indexing loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def rebuild_index(self):
        """Rebuild the message index."""
        db = SessionLocal()
        try:
            # Get messages that don't have index entries
            unindexed_messages = db.query(ROSMessage).outerjoin(
                MessageIndex, ROSMessage.id == MessageIndex.message_id
            ).filter(MessageIndex.id.is_(None)).all()
            
            if not unindexed_messages:
                logger.debug("No unindexed messages found")
                return
            
            logger.info(f"Indexing {len(unindexed_messages)} messages")
            
            for message in unindexed_messages:
                index_entry = MessageIndex.from_message(
                    message, 
                    message.recording_session_id
                )
                db.add(index_entry)
            
            db.commit()
            logger.info(f"Successfully indexed {len(unindexed_messages)} messages")
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def search_messages(
        self,
        topics: Optional[List[str]] = None,
        message_types: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        source_nodes: Optional[List[str]] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search for messages using various criteria."""
        db = SessionLocal()
        try:
            query = db.query(MessageIndex)
            
            # Apply filters
            if topics:
                query = query.filter(MessageIndex.topic_name.in_(topics))
            
            if message_types:
                query = query.filter(MessageIndex.message_type.in_(message_types))
            
            if start_time is not None:
                query = query.filter(MessageIndex.timestamp >= start_time)
            
            if end_time is not None:
                query = query.filter(MessageIndex.timestamp <= end_time)
            
            if source_nodes:
                query = query.filter(MessageIndex.source_node.in_(source_nodes))
            
            if min_size is not None:
                query = query.filter(MessageIndex.data_size >= min_size)
            
            if max_size is not None:
                query = query.filter(MessageIndex.data_size <= max_size)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            results = query.order_by(MessageIndex.timestamp.desc()).offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            messages = []
            for index_entry in results:
                messages.append({
                    'id': index_entry.message_id,
                    'topic_name': index_entry.topic_name,
                    'message_type': index_entry.message_type,
                    'timestamp': index_entry.timestamp,
                    'recording_session_id': index_entry.recording_session_id,
                    'source_node': index_entry.source_node,
                    'destination_node': index_entry.destination_node,
                    'data_size': index_entry.data_size,
                    'sequence_number': index_entry.sequence_number,
                    'year': index_entry.year,
                    'month': index_entry.month,
                    'day': index_entry.day,
                    'hour': index_entry.hour,
                    'minute': index_entry.minute,
                    'second': index_entry.second
                })
            
            return {
                'messages': messages,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        finally:
            db.close()
    
    async def get_topic_statistics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get statistics for all topics in a time range."""
        db = SessionLocal()
        try:
            query = db.query(
                MessageIndex.topic_name,
                MessageIndex.message_type,
                func.count(MessageIndex.id).label('message_count'),
                func.sum(MessageIndex.data_size).label('total_size'),
                func.avg(MessageIndex.data_size).label('avg_size'),
                func.min(MessageIndex.timestamp).label('first_seen'),
                func.max(MessageIndex.timestamp).label('last_seen')
            ).group_by(MessageIndex.topic_name, MessageIndex.message_type)
            
            if start_time is not None:
                query = query.filter(MessageIndex.timestamp >= start_time)
            
            if end_time is not None:
                query = query.filter(MessageIndex.timestamp <= end_time)
            
            results = query.all()
            
            statistics = []
            for result in results:
                duration = result.last_seen - result.first_seen if result.last_seen and result.first_seen else 0
                frequency = result.message_count / duration if duration > 0 else 0
                
                statistics.append({
                    'topic_name': result.topic_name,
                    'message_type': result.message_type,
                    'message_count': result.message_count,
                    'total_size': result.total_size or 0,
                    'avg_size': float(result.avg_size or 0),
                    'first_seen': result.first_seen,
                    'last_seen': result.last_seen,
                    'duration': duration,
                    'frequency_hz': frequency
                })
            
            return statistics
            
        finally:
            db.close()
    
    async def get_time_range_statistics(
        self,
        start_time: float,
        end_time: float,
        interval_seconds: int = 3600
    ) -> List[Dict[str, Any]]:
        """Get message statistics for time intervals."""
        db = SessionLocal()
        try:
            # Create time buckets
            current_time = start_time
            statistics = []
            
            while current_time < end_time:
                bucket_end = min(current_time + interval_seconds, end_time)
                
                # Count messages in this time bucket
                count = db.query(MessageIndex).filter(
                    and_(
                        MessageIndex.timestamp >= current_time,
                        MessageIndex.timestamp < bucket_end
                    )
                ).count()
                
                # Get total size in this bucket
                size_result = db.query(func.sum(MessageIndex.data_size)).filter(
                    and_(
                        MessageIndex.timestamp >= current_time,
                        MessageIndex.timestamp < bucket_end
                    )
                ).scalar()
                
                total_size = size_result or 0
                
                statistics.append({
                    'start_time': current_time,
                    'end_time': bucket_end,
                    'message_count': count,
                    'total_size': total_size,
                    'avg_size': total_size / count if count > 0 else 0
                })
                
                current_time = bucket_end
            
            return statistics
            
        finally:
            db.close()
    
    async def get_popular_topics(
        self,
        limit: int = 10,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get the most popular topics by message count."""
        db = SessionLocal()
        try:
            query = db.query(
                MessageIndex.topic_name,
                func.count(MessageIndex.id).label('message_count'),
                func.sum(MessageIndex.data_size).label('total_size')
            ).group_by(MessageIndex.topic_name).order_by(
                func.count(MessageIndex.id).desc()
            )
            
            if start_time is not None:
                query = query.filter(MessageIndex.timestamp >= start_time)
            
            if end_time is not None:
                query = query.filter(MessageIndex.timestamp <= end_time)
            
            results = query.limit(limit).all()
            
            return [
                {
                    'topic_name': result.topic_name,
                    'message_count': result.message_count,
                    'total_size': result.total_size or 0
                }
                for result in results
            ]
            
        finally:
            db.close()
    
    async def cleanup_old_indexes(self, days: int = 30):
        """Clean up old index entries."""
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Delete old index entries
            deleted_count = db.query(MessageIndex).filter(
                MessageIndex.timestamp < cutoff_timestamp
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old index entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old indexes: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get overall index statistics."""
        db = SessionLocal()
        try:
            total_entries = db.query(MessageIndex).count()
            total_messages = db.query(ROSMessage).count()
            
            # Get time range
            time_range = db.query(
                func.min(MessageIndex.timestamp),
                func.max(MessageIndex.timestamp)
            ).first()
            
            # Get unique topics and message types
            unique_topics = db.query(MessageIndex.topic_name).distinct().count()
            unique_types = db.query(MessageIndex.message_type).distinct().count()
            
            return {
                'total_index_entries': total_entries,
                'total_messages': total_messages,
                'index_coverage': (total_entries / total_messages * 100) if total_messages > 0 else 0,
                'earliest_timestamp': time_range[0] if time_range[0] else None,
                'latest_timestamp': time_range[1] if time_range[1] else None,
                'unique_topics': unique_topics,
                'unique_message_types': unique_types
            }
            
        finally:
            db.close() 