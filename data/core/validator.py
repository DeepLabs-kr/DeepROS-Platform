import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from ..config import DataSettings


logger = logging.getLogger(__name__)


class MessageValidator:
    """Message validation utilities for ROS messages."""
    
    def __init__(self, settings: Optional[DataSettings] = None):
        self.settings = settings or DataSettings()
        
        # Common ROS message types
        self.known_message_types = {
            'std_msgs/String',
            'std_msgs/Int32',
            'std_msgs/Float64',
            'std_msgs/Bool',
            'geometry_msgs/Twist',
            'geometry_msgs/Pose',
            'geometry_msgs/Point',
            'sensor_msgs/Image',
            'sensor_msgs/LaserScan',
            'nav_msgs/Odometry',
            'nav_msgs/Path',
            'tf2_msgs/TFMessage',
            'rosgraph_msgs/Log'
        }
        
        # Topic name patterns
        self.topic_patterns = [
            r'^[a-zA-Z_][a-zA-Z0-9_]*$',  # Basic topic name
            r'^/[a-zA-Z_][a-zA-Z0-9_/]*$',  # Absolute topic path
            r'^~[a-zA-Z_][a-zA-Z0-9_/]*$',  # Private topic path
        ]
    
    def validate_message(
        self,
        topic_name: str,
        message_type: str,
        data: bytes,
        timestamp: Optional[float] = None,
        source_node: Optional[str] = None,
        destination_node: Optional[str] = None,
        qos_profile: Optional[Dict[str, Any]] = None,
        header_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate a ROS message and return (is_valid, error_messages)."""
        errors = []
        
        # Validate topic name
        topic_valid, topic_errors = self._validate_topic_name(topic_name)
        if not topic_valid:
            errors.extend(topic_errors)
        
        # Validate message type
        type_valid, type_errors = self._validate_message_type(message_type)
        if not type_valid:
            errors.extend(type_errors)
        
        # Validate data
        data_valid, data_errors = self._validate_message_data(data)
        if not data_valid:
            errors.extend(data_errors)
        
        # Validate timestamp
        if timestamp is not None:
            time_valid, time_errors = self._validate_timestamp(timestamp)
            if not time_valid:
                errors.extend(time_errors)
        
        # Validate source node
        if source_node is not None:
            node_valid, node_errors = self._validate_node_name(source_node)
            if not node_valid:
                errors.extend(node_errors)
        
        # Validate destination node
        if destination_node is not None:
            node_valid, node_errors = self._validate_node_name(destination_node)
            if not node_valid:
                errors.extend(node_errors)
        
        # Validate QoS profile
        if qos_profile is not None:
            qos_valid, qos_errors = self._validate_qos_profile(qos_profile)
            if not qos_valid:
                errors.extend(qos_errors)
        
        # Validate header info
        if header_info is not None:
            header_valid, header_errors = self._validate_header_info(header_info)
            if not header_valid:
                errors.extend(header_errors)
        
        return len(errors) == 0, errors
    
    def _validate_topic_name(self, topic_name: str) -> Tuple[bool, List[str]]:
        """Validate ROS topic name."""
        errors = []
        
        if not topic_name:
            errors.append("Topic name cannot be empty")
            return False, errors
        
        if len(topic_name) > 255:
            errors.append("Topic name too long (max 255 characters)")
        
        # Check for invalid characters
        invalid_chars = ['\0', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in topic_name:
                errors.append(f"Topic name contains invalid character: {repr(char)}")
        
        # Check for valid ROS topic patterns
        import re
        is_valid_pattern = False
        for pattern in self.topic_patterns:
            if re.match(pattern, topic_name):
                is_valid_pattern = True
                break
        
        if not is_valid_pattern:
            errors.append("Topic name does not match valid ROS topic patterns")
        
        return len(errors) == 0, errors
    
    def _validate_message_type(self, message_type: str) -> Tuple[bool, List[str]]:
        """Validate ROS message type."""
        errors = []
        
        if not message_type:
            errors.append("Message type cannot be empty")
            return False, errors
        
        if len(message_type) > 255:
            errors.append("Message type too long (max 255 characters)")
        
        # Check for valid format (package/MessageType)
        if '/' not in message_type:
            errors.append("Message type must be in format 'package/MessageType'")
        
        # Check for invalid characters
        invalid_chars = ['\0', '\n', '\r', '\t', ' ', '\\']
        for char in invalid_chars:
            if char in message_type:
                errors.append(f"Message type contains invalid character: {repr(char)}")
        
        # Check if it's a known message type (optional warning)
        if message_type not in self.known_message_types:
            logger.debug(f"Unknown message type: {message_type}")
        
        return len(errors) == 0, errors
    
    def _validate_message_data(self, data: bytes) -> Tuple[bool, List[str]]:
        """Validate message data."""
        errors = []
        
        if data is None:
            errors.append("Message data cannot be None")
            return False, errors
        
        if not isinstance(data, bytes):
            errors.append("Message data must be bytes")
            return False, errors
        
        if len(data) == 0:
            errors.append("Message data cannot be empty")
        
        if len(data) > self.settings.MAX_MESSAGE_SIZE_BYTES:
            errors.append(f"Message data too large: {len(data)} bytes (max: {self.settings.MAX_MESSAGE_SIZE_BYTES})")
        
        return len(errors) == 0, errors
    
    def _validate_timestamp(self, timestamp: float) -> Tuple[bool, List[str]]:
        """Validate timestamp."""
        errors = []
        
        if not isinstance(timestamp, (int, float)):
            errors.append("Timestamp must be a number")
            return False, errors
        
        if timestamp < 0:
            errors.append("Timestamp cannot be negative")
        
        # Check if timestamp is reasonable (not too far in future/past)
        import time
        current_time = time.time()
        if timestamp > current_time + 86400:  # 1 day in future
            errors.append("Timestamp is too far in the future")
        
        if timestamp < current_time - 31536000:  # 1 year in past
            errors.append("Timestamp is too far in the past")
        
        return len(errors) == 0, errors
    
    def _validate_node_name(self, node_name: str) -> Tuple[bool, List[str]]:
        """Validate ROS node name."""
        errors = []
        
        if not node_name:
            errors.append("Node name cannot be empty")
            return False, errors
        
        if len(node_name) > 255:
            errors.append("Node name too long (max 255 characters)")
        
        # Check for invalid characters
        invalid_chars = ['\0', '\n', '\r', '\t', '/', '\\']
        for char in invalid_chars:
            if char in node_name:
                errors.append(f"Node name contains invalid character: {repr(char)}")
        
        # Check for valid ROS node name pattern
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', node_name):
            errors.append("Node name does not match valid ROS node name pattern")
        
        return len(errors) == 0, errors
    
    def _validate_qos_profile(self, qos_profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate QoS profile."""
        errors = []
        
        if not isinstance(qos_profile, dict):
            errors.append("QoS profile must be a dictionary")
            return False, errors
        
        # Check for required QoS fields
        required_fields = ['reliability', 'durability', 'history']
        for field in required_fields:
            if field not in qos_profile:
                errors.append(f"QoS profile missing required field: {field}")
        
        # Validate reliability
        if 'reliability' in qos_profile:
            reliability = qos_profile['reliability']
            valid_reliability = ['reliable', 'best_effort']
            if reliability not in valid_reliability:
                errors.append(f"Invalid reliability value: {reliability}")
        
        # Validate durability
        if 'durability' in qos_profile:
            durability = qos_profile['durability']
            valid_durability = ['volatile', 'transient_local']
            if durability not in valid_durability:
                errors.append(f"Invalid durability value: {durability}")
        
        # Validate history
        if 'history' in qos_profile:
            history = qos_profile['history']
            valid_history = ['keep_last', 'keep_all']
            if history not in valid_history:
                errors.append(f"Invalid history value: {history}")
        
        # Validate depth
        if 'depth' in qos_profile:
            depth = qos_profile['depth']
            if not isinstance(depth, int) or depth < 0:
                errors.append("QoS depth must be a non-negative integer")
        
        return len(errors) == 0, errors
    
    def _validate_header_info(self, header_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate header information."""
        errors = []
        
        if not isinstance(header_info, dict):
            errors.append("Header info must be a dictionary")
            return False, errors
        
        # Validate frame_id if present
        if 'frame_id' in header_info:
            frame_id = header_info['frame_id']
            if not isinstance(frame_id, str):
                errors.append("Header frame_id must be a string")
            elif len(frame_id) > 255:
                errors.append("Header frame_id too long (max 255 characters)")
        
        # Validate stamp if present
        if 'stamp' in header_info:
            stamp = header_info['stamp']
            if not isinstance(stamp, (int, float)):
                errors.append("Header stamp must be a number")
            elif stamp < 0:
                errors.append("Header stamp cannot be negative")
        
        return len(errors) == 0, errors
    
    def validate_recording_session(
        self,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate recording session parameters."""
        errors = []
        
        if not name:
            errors.append("Session name cannot be empty")
            return False, errors
        
        if len(name) > 255:
            errors.append("Session name too long (max 255 characters)")
        
        # Check for invalid characters in name
        invalid_chars = ['\0', '\n', '\r', '\t', '/', '\\']
        for char in invalid_chars:
            if char in name:
                errors.append(f"Session name contains invalid character: {repr(char)}")
        
        # Validate description
        if description is not None and len(description) > 1000:
            errors.append("Session description too long (max 1000 characters)")
        
        # Validate settings
        if settings is not None:
            settings_valid, settings_errors = self._validate_session_settings(settings)
            if not settings_valid:
                errors.extend(settings_errors)
        
        return len(errors) == 0, errors
    
    def _validate_session_settings(self, settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate recording session settings."""
        errors = []
        
        if not isinstance(settings, dict):
            errors.append("Session settings must be a dictionary")
            return False, errors
        
        # Validate compression settings
        if 'compression_enabled' in settings:
            if not isinstance(settings['compression_enabled'], bool):
                errors.append("compression_enabled must be a boolean")
        
        if 'compression_level' in settings:
            level = settings['compression_level']
            if not isinstance(level, int) or level < 0 or level > 9:
                errors.append("compression_level must be an integer between 0 and 9")
        
        # Validate batch settings
        if 'batch_size' in settings:
            batch_size = settings['batch_size']
            if not isinstance(batch_size, int) or batch_size < 1:
                errors.append("batch_size must be a positive integer")
        
        return len(errors) == 0, errors
    
    def get_validation_summary(self, validation_results: List[Tuple[bool, List[str]]]) -> Dict[str, Any]:
        """Get a summary of validation results."""
        total_valid = sum(1 for is_valid, _ in validation_results if is_valid)
        total_invalid = len(validation_results) - total_valid
        
        all_errors = []
        for _, errors in validation_results:
            all_errors.extend(errors)
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return {
            'total_messages': len(validation_results),
            'valid_messages': total_valid,
            'invalid_messages': total_invalid,
            'validation_rate': total_valid / len(validation_results) if validation_results else 0,
            'total_errors': len(all_errors),
            'error_counts': error_counts,
            'most_common_errors': sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        } 