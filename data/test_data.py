#!/usr/bin/env python3
"""
Test script for the ROS Data Storage System

This script demonstrates the functionality of the data storage system
by creating sample recording sessions and messages.
"""

import asyncio
import time
import json
import random
from typing import Dict, Any
from .config import DataSettings
from .core import ROSRecorder, ROSPlayer, MessageIndexer, MessageCompressor, MessageValidator
from .database import init_db


async def create_sample_messages() -> list:
    """Create sample ROS messages for testing."""
    messages = []
    
    # Sample message types and data
    message_types = [
        'std_msgs/String',
        'std_msgs/Int32', 
        'std_msgs/Float64',
        'geometry_msgs/Twist',
        'sensor_msgs/LaserScan',
        'nav_msgs/Odometry'
    ]
    
    topics = [
        '/cmd_vel',
        '/odom', 
        '/scan',
        '/imu',
        '/camera/image_raw',
        '/tf',
        '/rosout'
    ]
    
    nodes = [
        'robot_controller',
        'sensor_node',
        'navigation_node',
        'camera_node',
        'tf_broadcaster'
    ]
    
    base_time = time.time()
    
    for i in range(100):  # Create 100 sample messages
        message_type = random.choice(message_types)
        topic = random.choice(topics)
        source_node = random.choice(nodes)
        timestamp = base_time + i * 0.1  # 10Hz frequency
        
        # Create sample data based on message type
        if message_type == 'std_msgs/String':
            data = json.dumps({"data": f"Sample string message {i}"}).encode('utf-8')
        elif message_type == 'std_msgs/Int32':
            data = json.dumps({"data": random.randint(0, 1000)}).encode('utf-8')
        elif message_type == 'std_msgs/Float64':
            data = json.dumps({"data": random.uniform(0.0, 100.0)}).encode('utf-8')
        elif message_type == 'geometry_msgs/Twist':
            data = json.dumps({
                "linear": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": random.uniform(-1.0, 1.0)}
            }).encode('utf-8')
        elif message_type == 'sensor_msgs/LaserScan':
            # Simulate laser scan data
            ranges = [random.uniform(0.1, 10.0) for _ in range(360)]
            data = json.dumps({
                "ranges": ranges,
                "angle_min": -3.14159,
                "angle_max": 3.14159,
                "angle_increment": 0.0174533
            }).encode('utf-8')
        elif message_type == 'nav_msgs/Odometry':
            data = json.dumps({
                "pose": {
                    "pose": {
                        "position": {"x": random.uniform(-10.0, 10.0), "y": random.uniform(-10.0, 10.0), "z": 0.0},
                        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                    }
                },
                "twist": {
                    "twist": {
                        "linear": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": 0.0},
                        "angular": {"x": 0.0, "y": 0.0, "z": random.uniform(-1.0, 1.0)}
                    }
                }
            }).encode('utf-8')
        else:
            data = json.dumps({"data": f"Generic message {i}"}).encode('utf-8')
        
        messages.append({
            'topic_name': topic,
            'message_type': message_type,
            'data': data,
            'timestamp': timestamp,
            'source_node': source_node,
            'destination_node': None,
            'qos_profile': {
                'reliability': 'reliable',
                'durability': 'volatile',
                'history': 'keep_last',
                'depth': 10
            },
            'header_info': {
                'frame_id': 'base_link',
                'stamp': timestamp
            }
        })
    
    return messages


async def test_recording():
    """Test the recording functionality."""
    print("=== Testing Recording Functionality ===")
    
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    # Create sample messages
    messages = await create_sample_messages()
    
    # Start recording
    session = await recorder.start_recording(
        session_name="test_session",
        description="Test recording session with sample messages",
        settings={
            'compression_enabled': True,
            'compression_level': 6,
            'batch_size': 50
        }
    )
    
    print(f"Started recording session: {session.name} (ID: {session.id})")
    
    # Record messages
    for i, msg in enumerate(messages):
        success = await recorder.record_message(
            topic_name=msg['topic_name'],
            message_type=msg['message_type'],
            data=msg['data'],
            timestamp=msg['timestamp'],
            source_node=msg['source_node'],
            destination_node=msg['destination_node'],
            qos_profile=msg['qos_profile'],
            header_info=msg['header_info']
        )
        
        if not success:
            print(f"Failed to record message {i}")
        
        # Add some delay to simulate real-time recording
        await asyncio.sleep(0.01)
    
    # Stop recording
    session = await recorder.stop_recording()
    print(f"Recording completed: {session.total_messages} messages, {session.total_size_bytes} bytes")
    
    return session.id


async def test_playback(session_id: int):
    """Test the playback functionality."""
    print("\n=== Testing Playback Functionality ===")
    
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    # Message callback for playback
    played_messages = []
    
    async def message_callback(message):
        played_messages.append({
            'topic': message.topic_name,
            'type': message.message_type,
            'timestamp': message.timestamp,
            'size': message.data_size
        })
    
    # Start playback
    success = await player.play_session(
        session_id=session_id,
        playback_rate=2.0,  # 2x speed
        message_callback=message_callback
    )
    
    if not success:
        print("Failed to start playback")
        return
    
    # Wait for playback to complete
    while player.is_playing:
        stats = player.get_playback_stats()
        print(f"\rPlayback progress: {stats['progress_percent']:.1f}%", end='')
        await asyncio.sleep(0.1)
    
    print(f"\nPlayback completed: {len(played_messages)} messages played")
    
    # Show some played messages
    print("\nSample played messages:")
    for i, msg in enumerate(played_messages[:5]):
        print(f"  {i+1}. {msg['topic']} ({msg['type']}) at {msg['timestamp']:.3f}")


async def test_search():
    """Test the search functionality."""
    print("\n=== Testing Search Functionality ===")
    
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    # Search for messages
    result = await indexer.search_messages(
        topics=['/cmd_vel', '/odom'],
        limit=10
    )
    
    print(f"Found {result['total_count']} messages matching criteria")
    
    # Show search results
    print("\nSearch results:")
    for i, msg in enumerate(result['messages'][:5]):
        print(f"  {i+1}. {msg['topic_name']} ({msg['message_type']}) at {msg['timestamp']:.3f}")


async def test_compression():
    """Test the compression functionality."""
    print("\n=== Testing Compression Functionality ===")
    
    settings = DataSettings()
    compressor = MessageCompressor(settings)
    
    # Test data
    test_data = b"This is a test message that will be compressed to demonstrate the compression functionality of the ROS data storage system."
    
    # Test different compression methods
    methods = ['gzip', 'zlib', 'bz2', 'lzma']
    
    for method in methods:
        result = compressor.compress(test_data, method=method)
        print(f"{method}: {result['original_size']} -> {result['compressed_size']} bytes "
              f"(ratio: {result['compression_ratio']:.2f})")
    
    # Test decompression
    compressed = compressor.compress(test_data, method='gzip')
    decompressed = compressor.decompress(compressed['data'], method='gzip')
    
    if decompressed['data'] == test_data:
        print("Compression/decompression test: PASSED")
    else:
        print("Compression/decompression test: FAILED")


async def test_validation():
    """Test the validation functionality."""
    print("\n=== Testing Validation Functionality ===")
    
    settings = DataSettings()
    validator = MessageValidator(settings)
    
    # Test valid message
    valid_result = validator.validate_message(
        topic_name="/test_topic",
        message_type="std_msgs/String",
        data=b"test data",
        timestamp=time.time(),
        source_node="test_node"
    )
    
    print(f"Valid message validation: {'PASSED' if valid_result[0] else 'FAILED'}")
    if not valid_result[0]:
        print(f"  Errors: {valid_result[1]}")
    
    # Test invalid message
    invalid_result = validator.validate_message(
        topic_name="",  # Invalid: empty topic name
        message_type="invalid_type",  # Invalid: no package prefix
        data=b"",  # Invalid: empty data
        timestamp=-1.0  # Invalid: negative timestamp
    )
    
    print(f"Invalid message validation: {'PASSED' if not invalid_result[0] else 'FAILED'}")
    if invalid_result[1]:
        print(f"  Errors: {invalid_result[1]}")


async def test_statistics():
    """Test the statistics functionality."""
    print("\n=== Testing Statistics Functionality ===")
    
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    # Get index statistics
    index_stats = indexer.get_index_statistics()
    print(f"Index Statistics:")
    print(f"  Total entries: {index_stats['total_index_entries']}")
    print(f"  Total messages: {index_stats['total_messages']}")
    print(f"  Index coverage: {index_stats['index_coverage']:.1f}%")
    print(f"  Unique topics: {index_stats['unique_topics']}")
    print(f"  Unique message types: {index_stats['unique_message_types']}")
    
    # Get topic statistics
    topic_stats = await indexer.get_topic_statistics()
    if topic_stats:
        print(f"\nTopic Statistics:")
        for i, topic in enumerate(topic_stats[:5]):
            print(f"  {i+1}. {topic['topic_name']}: {topic['message_count']} messages, "
                  f"avg size: {topic['avg_size']:.1f} bytes")


async def run_tests():
    """Run all tests."""
    print("ROS Data Storage System - Test Suite")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    try:
        # Test recording
        session_id = await test_recording()
        
        # Test playback
        await test_playback(session_id)
        
        # Test search
        await test_search()
        
        # Test compression
        await test_compression()
        
        # Test validation
        await test_validation()
        
        # Test statistics
        await test_statistics()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_tests()) 