from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
import json


@dataclass
class Message:
    """Represents an MQTT message"""
    
    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False
    dup: bool = False
    
    # Message metadata
    message_id: Optional[int] = None
    timestamp: datetime = None
    client_id: Optional[str] = None
    
    # ROS-specific fields
    ros_domain: Optional[str] = None
    ros_node: Optional[str] = None
    ros_message_type: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    @property
    def payload_str(self) -> str:
        """Get payload as string"""
        try:
            return self.payload.decode('utf-8')
        except UnicodeDecodeError:
            return str(self.payload)
    
    @property
    def payload_json(self) -> Optional[Any]:
        """Get payload as JSON object"""
        try:
            return json.loads(self.payload_str)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    def to_dict(self) -> dict:
        """Convert message to dictionary"""
        return {
            'topic': self.topic,
            'payload': self.payload_str,
            'qos': self.qos,
            'retain': self.retain,
            'dup': self.dup,
            'message_id': self.message_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'client_id': self.client_id,
            'ros_domain': self.ros_domain,
            'ros_node': self.ros_node,
            'ros_message_type': self.ros_message_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create message from dictionary"""
        timestamp = None
        if data.get('timestamp'):
            try:
                timestamp = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pass
        
        return cls(
            topic=data['topic'],
            payload=data['payload'].encode('utf-8') if isinstance(data['payload'], str) else data['payload'],
            qos=data.get('qos', 0),
            retain=data.get('retain', False),
            dup=data.get('dup', False),
            message_id=data.get('message_id'),
            timestamp=timestamp,
            client_id=data.get('client_id'),
            ros_domain=data.get('ros_domain'),
            ros_node=data.get('ros_node'),
            ros_message_type=data.get('ros_message_type'),
        )
    
    def is_ros_message(self) -> bool:
        """Check if this is a ROS-related message"""
        return bool(self.ros_domain or self.ros_node or self.ros_message_type)
    
    def extract_ros_info(self):
        """Extract ROS information from topic"""
        if not self.topic.startswith('ros/'):
            return
        
        parts = self.topic.split('/')
        if len(parts) >= 3:
            self.ros_domain = parts[1]
            self.ros_node = parts[2]
            if len(parts) >= 4:
                self.ros_message_type = parts[3] 