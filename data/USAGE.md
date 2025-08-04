# ROS Data Storage System - Usage Guide

This guide shows how to use the ROS Data Storage System with actual rosbag-like functionality.

## Quick Start

### 1. Basic Recording

```bash
# Start recording ROS messages
python -m data.main record --name "my_session" --topics "/cmd_vel,/odom,/scan"

# Stop recording with Ctrl+C
```

### 2. Basic Playback

```bash
# List available sessions
python -m data.main list

# Play back a specific session
python -m data.main play --session-id 1 --topics "/cmd_vel,/odom"

# Play back with 2x speed
python -m data.main play --session-id 1 --rate 2.0
```

### 3. Search and Analysis

```bash
# Search for specific messages
python -m data.main search --topics "/cmd_vel" --start-time 1234567890

# Get session information
python -m data.main info --session-id 1

# View statistics
python -m data.main stats
```

## Advanced Usage

### Recording with Compression

```bash
# Record with gzip compression
python -m data.main record --name "compressed_session" \
    --topics "/cmd_vel,/odom,/scan" \
    --compression \
    --compression-level 9
```

### Filtered Playback

```bash
# Play back only specific topics
python -m data.main play --session-id 1 --topics "/cmd_vel,/odom"

# Play back specific time range
python -m data.main play --session-id 1 \
    --start-time 1234567890 \
    --end-time 1234568000

# Loop playback
python -m data.main play --session-id 1 --loop
```

### Advanced Search

```bash
# Search by message type
python -m data.main search --message-types "geometry_msgs/Twist"

# Search by time range
python -m data.main search --start-time 1234567890 --end-time 1234568000

# Search by source node
python -m data.main search --source-nodes "robot_controller"

# Search by message size
python -m data.main search --min-size 100 --max-size 1000
```

## Python API Usage

### Recording Messages

```python
import asyncio
import time
import json
from data.core import ROSRecorder
from data.config import DataSettings

async def record_ros_messages():
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    # Start recording session
    session = await recorder.start_recording(
        session_name="python_demo",
        description="Recording from Python API",
        topics=["/cmd_vel", "/odom", "/scan"]
    )
    
    print(f"Started recording session: {session.id}")
    
    # Record some messages
    for i in range(100):
        # Simulate cmd_vel message
        cmd_vel_data = json.dumps({
            "linear": {"x": 0.5, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.1}
        }).encode('utf-8')
        
        await recorder.record_message(
            topic_name="/cmd_vel",
            message_type="geometry_msgs/Twist",
            data=cmd_vel_data,
            timestamp=time.time(),
            source_node="robot_controller"
        )
        
        await asyncio.sleep(0.1)  # 10Hz
    
    # Stop recording
    final_session = await recorder.stop_recording()
    print(f"Recorded {final_session.total_messages} messages")

asyncio.run(record_ros_messages())
```

### Playing Back Messages

```python
import asyncio
from data.core import ROSPlayer
from data.config import DataSettings

async def play_ros_messages():
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    # Message callback function
    async def message_callback(message):
        print(f"Playing: {message.topic_name} at {message.timestamp:.3f}")
        # Process the message data here
        # message.data contains the binary message data
    
    # Start playback
    success = await player.play_session(
        session_id=1,
        topics=["/cmd_vel", "/odom"],
        playback_rate=1.0,
        message_callback=message_callback
    )
    
    if success:
        print("Playback started")
        # Wait for completion
        while player.is_playing:
            stats = player.get_playback_stats()
            print(f"Progress: {stats['progress_percent']:.1f}%")
            await asyncio.sleep(0.1)

asyncio.run(play_ros_messages())
```

### Searching Messages

```python
import asyncio
from data.core import MessageIndexer
from data.config import DataSettings

async def search_messages():
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    # Search for messages
    results = await indexer.search_messages(
        topics=["/cmd_vel"],
        start_time=1234567890,
        end_time=1234568000,
        limit=100
    )
    
    print(f"Found {results['total_count']} messages")
    
    for msg in results['messages']:
        print(f"Topic: {msg['topic_name']}, Time: {msg['timestamp']}")
    
    # Get topic statistics
    stats = await indexer.get_topic_statistics()
    for stat in stats:
        print(f"{stat['topic_name']}: {stat['message_count']} messages")

asyncio.run(search_messages())
```

### Compression and Validation

```python
import asyncio
from data.core import MessageCompressor, MessageValidator
from data.config import DataSettings

async def compression_demo():
    settings = DataSettings()
    compressor = MessageCompressor(settings)
    validator = MessageValidator(settings)
    
    # Sample message data
    message_data = b"This is a sample ROS message that will be compressed"
    
    # Validate message
    is_valid, errors = validator.validate_message(
        topic_name="/test_topic",
        message_type="std_msgs/String",
        data=message_data,
        timestamp=time.time(),
        source_node="test_node"
    )
    
    if is_valid:
        print("Message is valid")
        
        # Compress message
        compressed = compressor.compress(message_data, method='gzip')
        print(f"Original: {len(message_data)} bytes")
        print(f"Compressed: {compressed['compressed_size']} bytes")
        print(f"Compression ratio: {compressed['compression_ratio']:.2f}")
        
        # Decompress message
        decompressed = compressor.decompress(compressed['data'])
        print(f"Decompressed: {len(decompressed['data'])} bytes")
        
        # Verify integrity
        if decompressed['data'] == message_data:
            print("Compression/decompression successful")

asyncio.run(compression_demo())
```

## Integration with MQTT Broker

### Recording MQTT Messages as ROS Data

```python
import asyncio
from data.mqtt_integration import MQTTDataRecorder

async def mqtt_recording_demo():
    recorder = MQTTDataRecorder()
    
    try:
        # Start the system
        await recorder.start()
        
        # Start recording MQTT messages
        await recorder.start_recording(
            session_name="mqtt_session",
            topics=["ros/demo/robot/cmd_vel", "ros/demo/robot/odom"]
        )
        
        # Publish some test messages
        await recorder.broker.publish(
            topic="ros/demo/robot/cmd_vel",
            payload=b'{"linear": {"x": 0.5}, "angular": {"z": 0.1}}',
            qos=1
        )
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Stop recording
        session = await recorder.stop_recording()
        print(f"Recorded {session.total_messages} messages")
        
    finally:
        await recorder.stop()

asyncio.run(mqtt_recording_demo())
```

### Playing Back to MQTT

```python
import asyncio
from data.mqtt_integration import MQTTDataPlayer

async def mqtt_playback_demo():
    player = MQTTDataPlayer()
    
    try:
        # Start the system
        await player.start()
        
        # Play back recorded messages to MQTT
        await player.play_session(
            session_id=1,
            topics=["ros/demo/robot/cmd_vel"],
            playback_rate=1.0
        )
        
    finally:
        await player.stop()

asyncio.run(mqtt_playback_demo())
```

## Real-World Scenarios

### Scenario 1: Robot Navigation Recording

```bash
# Record robot navigation data
python -m data.main record --name "navigation_test" \
    --topics "/cmd_vel,/odom,/scan,/tf,/map" \
    --compression \
    --compression-level 6

# Later, analyze the recording
python -m data.main info --session-id 1
python -m data.main search --topics "/cmd_vel" --start-time 1234567890
```

### Scenario 2: Sensor Data Analysis

```bash
# Record sensor data
python -m data.main record --name "sensor_data" \
    --topics "/camera/image_raw,/imu,/gps" \
    --compression

# Search for specific sensor events
python -m data.main search --message-types "sensor_msgs/Image" \
    --start-time 1234567890 \
    --end-time 1234568000
```

### Scenario 3: System Performance Monitoring

```bash
# Record system performance data
python -m data.main record --name "performance_monitor" \
    --topics "/rosout,/diagnostics,/tf" \
    --compression

# Analyze system performance
python -m data.main stats
python -m data.main search --topics "/rosout" --source-nodes "robot_controller"
```

## Configuration

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
DATA_LOG_FILE=./data.log
```

### Custom Configuration

```python
from data.config import DataSettings

# Custom settings
settings = DataSettings(
    DATABASE_URL="sqlite:///./custom_ros_data.db",
    COMPRESSION_ENABLED=True,
    COMPRESSION_LEVEL=9,
    BATCH_SIZE=500,
    MAX_MESSAGE_SIZE_BYTES=20 * 1024 * 1024  # 20MB
)

# Use custom settings
recorder = ROSRecorder(settings)
```

## Troubleshooting

### Common Issues

1. **Database locked error**
   ```bash
   # Check if another process is using the database
   # Close any open database connections
   ```

2. **Memory usage high**
   ```bash
   # Reduce batch size
   python -m data.main record --batch-size 100
   ```

3. **Compression not working**
   ```bash
   # Check if compression is enabled
   python -m data.main record --compression
   ```

4. **Search not finding messages**
   ```bash
   # Rebuild index
   python -m data.main index --rebuild
   ```

### Performance Tips

1. **Use appropriate batch sizes** for your system
2. **Enable compression** for large message volumes
3. **Use topic filtering** to reduce storage requirements
4. **Regular index maintenance** for large datasets
5. **Monitor disk space** for long recording sessions

## Best Practices

1. **Use descriptive session names** for easy identification
2. **Record only necessary topics** to save storage space
3. **Use compression** for large message volumes
4. **Regular backup** of important recordings
5. **Monitor system resources** during long recordings
6. **Use appropriate QoS settings** for critical messages
7. **Validate messages** before recording
8. **Use time-based filtering** for efficient playback 