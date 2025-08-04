# ROS Data Storage System

A comprehensive rosbag-like system for storing and managing ROS messages using SQLite database with advanced indexing, search, and compression capabilities.

## Features

### Core Functionality
- **Message Recording**: Record ROS messages with metadata and timestamps
- **Message Playback**: Play back recorded messages with configurable rates and filtering
- **Session Management**: Organize recordings into named sessions with statistics
- **Real-time Processing**: Asynchronous message processing with batch operations

### Advanced Features
- **Message Indexing**: Fast search and retrieval using time-based and content-based indexes
- **Compression**: Multiple compression algorithms (gzip, zlib, bz2, lzma) with auto-detection
- **Message Validation**: Comprehensive validation of ROS messages and metadata
- **Statistics**: Detailed statistics and analytics for recordings and topics
- **Search**: Advanced search capabilities with multiple criteria

### Database Features
- **SQLite Storage**: Lightweight, embedded database for message storage
- **Optimized Schema**: Efficient database design with proper indexing
- **Transaction Support**: ACID-compliant operations for data integrity
- **Automatic Cleanup**: Configurable cleanup of old data and indexes

## Installation

The data storage system is part of the DeepROS Platform. Install dependencies using `uv`:

```bash
uv sync
```

## Quick Start

### Basic Recording

```python
import asyncio
from data.core import ROSRecorder
from data.config import DataSettings

async def record_messages():
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    # Start recording
    session = await recorder.start_recording(
        session_name="my_session",
        description="Test recording"
    )
    
    # Record a message
    await recorder.record_message(
        topic_name="/cmd_vel",
        message_type="geometry_msgs/Twist",
        data=b"message_data_here",
        timestamp=time.time()
    )
    
    # Stop recording
    await recorder.stop_recording()

asyncio.run(record_messages())
```

### Basic Playback

```python
import asyncio
from data.core import ROSPlayer
from data.config import DataSettings

async def play_messages():
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    # Message callback
    async def message_callback(message):
        print(f"Playing: {message.topic_name}")
    
    # Start playback
    await player.play_session(
        session_id=1,
        message_callback=message_callback
    )

asyncio.run(play_messages())
```

## Command Line Interface

The system provides a comprehensive command-line interface similar to rosbag:

### Recording

```bash
# Start recording
python -m data.main record --name "test_session" --topics "/cmd_vel,/odom"

# Record with compression
python -m data.main record --name "compressed_session" --compression --compression-level 9

# Record with custom batch size
python -m data.main record --name "batch_session" --batch-size 500
```

### Playback

```bash
# Play a session
python -m data.main play --session-id 1

# Play specific topics
python -m data.main play --session-id 1 --topics "/cmd_vel"

# Play with custom rate
python -m data.main play --session-id 1 --rate 2.0

# Play time range
python -m data.main play --session-id 1 --start-time 1234567890 --end-time 1234567990
```

### Information and Management

```bash
# List all sessions
python -m data.main list

# Show session information
python -m data.main info --session-id 1

# Search for messages
python -m data.main search --topics "/cmd_vel" --start-time 1234567890

# Show statistics
python -m data.main stats
```

### Advanced Operations

```bash
# Validate messages
python -m data.main validate

# Show compression methods
python -m data.main compress --method info

# Manage indexing
python -m data.main index --action rebuild
python -m data.main index --action cleanup --days 30
```

## API Reference

### Core Classes

#### ROSRecorder

Main class for recording ROS messages.

```python
class ROSRecorder:
    async def start_recording(
        self, 
        session_name: str, 
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> RecordingSession
    
    async def stop_recording(self) -> Optional[RecordingSession]
    
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
    ) -> bool
    
    def get_recording_stats(self) -> Dict[str, Any]
    
    def list_sessions(self, active_only: bool = False) -> List[RecordingSession]
    
    def delete_session(self, session_id: int) -> bool
```

#### ROSPlayer

Main class for playing back recorded messages.

```python
class ROSPlayer:
    async def play_session(
        self,
        session_id: int,
        topics: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        playback_rate: Optional[float] = None,
        loop: Optional[bool] = None,
        message_callback: Optional[Callable] = None
    ) -> bool
    
    async def stop_playback(self)
    
    async def pause_playback(self)
    
    async def resume_playback(self)
    
    def seek_to_time(self, timestamp: float) -> bool
    
    def get_playback_stats(self) -> Dict[str, Any]
    
    def get_session_info(self, session_id: int) -> Optional[Dict[str, Any]]
    
    def list_sessions(self) -> List[Dict[str, Any]]
```

#### MessageIndexer

Class for message indexing and search functionality.

```python
class MessageIndexer:
    async def start_auto_indexing(self)
    
    async def stop_auto_indexing(self)
    
    async def rebuild_index(self)
    
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
    ) -> Dict[str, Any]
    
    async def get_topic_statistics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]
    
    async def get_popular_topics(
        self,
        limit: int = 10,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]
    
    def get_index_statistics(self) -> Dict[str, Any]
```

#### MessageCompressor

Class for message compression and decompression.

```python
class MessageCompressor:
    def compress(
        self, 
        data: bytes, 
        method: Optional[str] = None, 
        level: Optional[int] = None
    ) -> Dict[str, Any]
    
    def decompress(
        self, 
        data: bytes, 
        method: Optional[str] = None
    ) -> Dict[str, Any]
    
    def get_compression_stats(self, data: bytes) -> Dict[str, Any]
    
    def optimize_compression(
        self, 
        data: bytes, 
        target_ratio: float = 0.5,
        max_time_seconds: float = 5.0
    ) -> Dict[str, Any]
    
    def get_method_info(self, method: str) -> Dict[str, Any]
```

#### MessageValidator

Class for message validation.

```python
class MessageValidator:
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
    ) -> Tuple[bool, List[str]]
    
    def validate_recording_session(
        self,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]
    
    def get_validation_summary(self, validation_results: List[Tuple[bool, List[str]]]) -> Dict[str, Any]
```

### Database Models

#### ROSMessage

Represents a single ROS message in the database.

```python
class ROSMessage(Base):
    id: int
    topic_name: str
    message_type: str
    timestamp: float
    sequence_number: int
    data: bytes
    data_size: int
    recording_session_id: int
    source_node: Optional[str]
    destination_node: Optional[str]
    qos_profile: Optional[str]  # JSON string
    header_info: Optional[str]  # JSON string
    created_at: datetime
    updated_at: datetime
```

#### RecordingSession

Represents a recording session.

```python
class RecordingSession(Base):
    id: int
    name: str
    description: Optional[str]
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    is_active: bool
    is_compressed: bool
    total_messages: int
    total_size_bytes: int
    topics_count: int
    settings: Optional[str]  # JSON string
    created_at: datetime
    updated_at: datetime
```

#### TopicInfo

Represents topic metadata and statistics.

```python
class TopicInfo(Base):
    id: int
    topic_name: str
    message_type: str
    total_messages: int
    total_size_bytes: int
    first_seen: Optional[float]
    last_seen: Optional[float]
    avg_frequency_hz: float
    avg_message_size: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### MessageIndex

Represents an index entry for fast message retrieval.

```python
class MessageIndex(Base):
    id: int
    message_id: int
    topic_name: str
    message_type: str
    timestamp: float
    recording_session_id: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    source_node: Optional[str]
    destination_node: Optional[str]
    data_size: int
    sequence_number: int
    created_at: datetime
```

## Configuration

The system is configured through the `DataSettings` class and environment variables:

### Environment Variables

```bash
# Database settings
DATA_DATABASE_URL=sqlite:///./ros_data.db
DATA_DATABASE_ECHO=false

# Storage settings
DATA_DATA_DIR=./data_storage
DATA_MAX_FILE_SIZE_MB=1000
DATA_COMPRESSION_ENABLED=true
DATA_COMPRESSION_LEVEL=6

# Message settings
DATA_MAX_MESSAGE_SIZE_BYTES=10485760
DATA_MESSAGE_TIMEOUT_SECONDS=30
DATA_BATCH_SIZE=1000

# Recording settings
DATA_DEFAULT_RECORDING_DURATION=3600
DATA_AUTO_SPLIT_RECORDINGS=true
DATA_SPLIT_INTERVAL_SECONDS=3600

# Playback settings
DATA_DEFAULT_PLAYBACK_RATE=1.0
DATA_LOOP_PLAYBACK=false
DATA_START_TIME_OFFSET=0.0

# Indexing settings
DATA_AUTO_INDEX_ENABLED=true
DATA_INDEX_INTERVAL_SECONDS=60

# Logging settings
DATA_LOG_LEVEL=INFO
DATA_LOG_FILE=
```

### Configuration Class

```python
from data.config import DataSettings

settings = DataSettings(
    DATABASE_URL="sqlite:///./custom_data.db",
    COMPRESSION_ENABLED=True,
    BATCH_SIZE=500
)
```

## Testing

Run the test suite to verify functionality:

```bash
python -m data.test_data
```

The test suite includes:
- Recording and playback tests
- Search functionality tests
- Compression tests
- Validation tests
- Statistics tests

## Performance Considerations

### Database Optimization
- Use appropriate indexes for your query patterns
- Consider database size limits and cleanup policies
- Monitor index coverage and rebuild when necessary

### Memory Management
- Configure appropriate batch sizes for your use case
- Use compression for large messages
- Monitor memory usage during long recording sessions

### Storage Optimization
- Enable compression for better storage efficiency
- Configure automatic cleanup of old data
- Monitor disk space usage

## Troubleshooting

### Common Issues

1. **Database locked errors**: Ensure only one process accesses the database at a time
2. **Memory issues**: Reduce batch size or enable compression
3. **Slow queries**: Rebuild indexes or add appropriate indexes
4. **Large file sizes**: Enable compression or increase file size limits

### Debugging

Enable debug logging:

```bash
python -m data.main --log-level DEBUG <command>
```

### Performance Monitoring

Use the statistics commands to monitor system performance:

```bash
python -m data.main stats
python -m data.main index --action rebuild
```

## Contributing

When contributing to the data storage system:

1. Follow the existing code style and patterns
2. Add appropriate tests for new functionality
3. Update documentation for new features
4. Consider performance implications of changes
5. Ensure database schema compatibility

## License

This project is part of the DeepROS Platform and follows the same licensing terms. 