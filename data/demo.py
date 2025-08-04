#!/usr/bin/env python3
"""
ROS Data Storage System - Demonstration Script

This script demonstrates the rosbag-like functionality of the data storage system
by creating sample ROS messages, recording them, and then playing them back.
"""

import asyncio
import time
import json
import random
from typing import Dict, Any
from .config import DataSettings
from .core import ROSRecorder, ROSPlayer, MessageIndexer, MessageCompressor, MessageValidator
from .database import init_db


async def create_rosbag_like_data():
    """Create sample ROS messages that mimic real rosbag data."""
    messages = []
    
    # Realistic ROS message types and topics
    message_types = [
        'std_msgs/String',
        'std_msgs/Int32', 
        'std_msgs/Float64',
        'std_msgs/Bool',
        'geometry_msgs/Twist',
        'geometry_msgs/Pose',
        'geometry_msgs/Point',
        'sensor_msgs/LaserScan',
        'sensor_msgs/Image',
        'nav_msgs/Odometry',
        'nav_msgs/Path',
        'tf2_msgs/TFMessage',
        'rosgraph_msgs/Log'
    ]
    
    topics = [
        '/cmd_vel',
        '/odom', 
        '/scan',
        '/imu',
        '/camera/image_raw',
        '/camera/depth/image_raw',
        '/tf',
        '/tf_static',
        '/rosout',
        '/diagnostics',
        '/robot_description',
        '/move_base/status',
        '/amcl_pose'
    ]
    
    nodes = [
        'robot_controller',
        'sensor_node',
        'navigation_node',
        'camera_node',
        'tf_broadcaster',
        'move_base',
        'amcl',
        'gmapping',
        'rviz'
    ]
    
    base_time = time.time()
    
    print("Creating sample ROS messages...")
    
    for i in range(200):  # Create 200 sample messages
        message_type = random.choice(message_types)
        topic = random.choice(topics)
        source_node = random.choice(nodes)
        timestamp = base_time + i * 0.05  # 20Hz frequency
        
        # Create realistic data based on message type
        if message_type == 'std_msgs/String':
            data = json.dumps({"data": f"ROS message {i} from {source_node}"}).encode('utf-8')
        elif message_type == 'std_msgs/Int32':
            data = json.dumps({"data": random.randint(0, 1000)}).encode('utf-8')
        elif message_type == 'std_msgs/Float64':
            data = json.dumps({"data": random.uniform(0.0, 100.0)}).encode('utf-8')
        elif message_type == 'std_msgs/Bool':
            data = json.dumps({"data": random.choice([True, False])}).encode('utf-8')
        elif message_type == 'geometry_msgs/Twist':
            data = json.dumps({
                "linear": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": random.uniform(-1.0, 1.0)}
            }).encode('utf-8')
        elif message_type == 'geometry_msgs/Pose':
            data = json.dumps({
                "position": {"x": random.uniform(-10.0, 10.0), "y": random.uniform(-10.0, 10.0), "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": random.uniform(-1.0, 1.0), "w": random.uniform(0.0, 1.0)}
            }).encode('utf-8')
        elif message_type == 'sensor_msgs/LaserScan':
            # Simulate realistic laser scan data
            ranges = [random.uniform(0.1, 10.0) for _ in range(360)]
            data = json.dumps({
                "header": {"frame_id": "laser", "stamp": timestamp},
                "ranges": ranges,
                "angle_min": -3.14159,
                "angle_max": 3.14159,
                "angle_increment": 0.0174533,
                "range_min": 0.1,
                "range_max": 10.0
            }).encode('utf-8')
        elif message_type == 'nav_msgs/Odometry':
            data = json.dumps({
                "header": {"frame_id": "odom", "stamp": timestamp},
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
        elif message_type == 'tf2_msgs/TFMessage':
            data = json.dumps({
                "transforms": [{
                    "header": {"frame_id": "map", "stamp": timestamp},
                    "child_frame_id": "base_link",
                    "transform": {
                        "translation": {"x": random.uniform(-10.0, 10.0), "y": random.uniform(-10.0, 10.0), "z": 0.0},
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                    }
                }]
            }).encode('utf-8')
        else:
            data = json.dumps({"data": f"Generic {message_type} message {i}"}).encode('utf-8')
        
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
    
    print(f"Created {len(messages)} sample messages")
    return messages


async def demonstrate_recording(messages: list):
    """Demonstrate recording functionality similar to rosbag record."""
    print("\n=== ROS Data Recording Demo ===")
    
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    try:
        # Start recording session
        session = await recorder.start_recording(
            session_name="demo_session",
            description="Demonstration recording session with sample ROS messages",
            topics=['/cmd_vel', '/odom', '/scan', '/tf'],
            settings={
                'compression_enabled': True,
                'compression_level': 6,
                'batch_size': 50
            }
        )
        
        print(f"Started recording session: {session.name} (ID: {session.id})")
        
        # Record messages with realistic timing
        for i, message_data in enumerate(messages):
            success = await recorder.record_message(
                topic_name=message_data['topic_name'],
                message_type=message_data['message_type'],
                data=message_data['data'],
                timestamp=message_data['timestamp'],
                source_node=message_data['source_node'],
                destination_node=message_data['destination_node'],
                qos_profile=message_data['qos_profile'],
                header_info=message_data['header_info']
            )
            
            if success:
                if i % 50 == 0:
                    stats = recorder.get_recording_stats()
                    print(f"Recorded {stats['total_messages']} messages, "
                          f"Size: {stats['total_size_bytes']} bytes")
            
            # Simulate real-time recording
            await asyncio.sleep(0.01)
        
        # Stop recording
        final_session = await recorder.stop_recording()
        
        if final_session:
            print(f"\nRecording completed:")
            print(f"  Session: {final_session.name}")
            print(f"  Duration: {final_session.duration:.2f} seconds")
            print(f"  Total messages: {final_session.total_messages}")
            print(f"  Total size: {final_session.total_size_bytes} bytes")
            print(f"  Topics: {final_session.topics_count}")
            print(f"  Compressed: {final_session.is_compressed}")
        
        return final_session.id if final_session else None
        
    except Exception as e:
        print(f"Error during recording: {e}")
        await recorder.stop_recording()
        return None


async def demonstrate_playback(session_id: int):
    """Demonstrate playback functionality similar to rosbag play."""
    print("\n=== ROS Data Playback Demo ===")
    
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    # Message callback for playback
    async def message_callback(message):
        print(f"  Playing: {message.topic_name} ({message.message_type}) "
              f"at {message.timestamp:.3f}")
    
    try:
        # Start playback
        success = await player.play_session(
            session_id=session_id,
            topics=['/cmd_vel', '/odom'],  # Filter specific topics
            playback_rate=2.0,  # 2x speed
            loop=False,
            message_callback=message_callback
        )
        
        if not success:
            print("Failed to start playback")
            return
        
        print("Playback started (2x speed, filtered topics)")
        
        # Monitor playback progress
        while player.is_playing:
            stats = player.get_playback_stats()
            print(f"\rProgress: {stats['progress_percent']:.1f}% "
                  f"({stats['played_messages']}/{stats['total_messages']})", end='')
            await asyncio.sleep(0.1)
        
        print("\nPlayback completed")
        
    except Exception as e:
        print(f"Error during playback: {e}")
        await player.stop_playback()


async def demonstrate_search():
    """Demonstrate search functionality."""
    print("\n=== ROS Data Search Demo ===")
    
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    try:
        # Search for messages
        print("Searching for /cmd_vel messages...")
        results = await indexer.search_messages(
            topics=['/cmd_vel'],
            limit=10
        )
        
        print(f"Found {results['total_count']} /cmd_vel messages")
        for msg in results['messages'][:5]:  # Show first 5
            print(f"  {msg['topic_name']} at {msg['timestamp']:.3f}")
        
        # Get topic statistics
        print("\nGetting topic statistics...")
        stats = await indexer.get_topic_statistics()
        
        print("Top topics by message count:")
        for stat in stats[:5]:
            print(f"  {stat['topic_name']}: {stat['message_count']} messages, "
                  f"{stat['frequency_hz']:.1f} Hz")
        
    except Exception as e:
        print(f"Error during search: {e}")


async def demonstrate_compression():
    """Demonstrate compression functionality."""
    print("\n=== ROS Data Compression Demo ===")
    
    settings = DataSettings()
    compressor = MessageCompressor(settings)
    
    # Create sample data
    sample_data = b"This is a sample ROS message data that will be compressed to demonstrate the compression capabilities of the system. " * 100
    
    print(f"Original data size: {len(sample_data)} bytes")
    
    # Test different compression methods
    methods = ['gzip', 'zlib', 'bz2', 'lzma']
    
    for method in methods:
        result = compressor.compress(sample_data, method=method)
        print(f"{method.upper()}: {result['compressed_size']} bytes "
              f"(ratio: {result['compression_ratio']:.2f})")
    
    # Test auto-detection
    compressed = compressor.compress(sample_data, method='gzip')
    decompressed = compressor.decompress(compressed['data'])
    
    print(f"Auto-detection test: {len(decompressed['data'])} bytes "
          f"(original: {len(sample_data)} bytes)")


async def demonstrate_validation():
    """Demonstrate message validation."""
    print("\n=== ROS Data Validation Demo ===")
    
    settings = DataSettings()
    validator = MessageValidator(settings)
    
    # Test valid message
    is_valid, errors = validator.validate_message(
        topic_name="/cmd_vel",
        message_type="geometry_msgs/Twist",
        data=b"valid_message_data",
        timestamp=time.time(),
        source_node="robot_controller"
    )
    
    print(f"Valid message test: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test invalid message
    is_valid, errors = validator.validate_message(
        topic_name="",  # Invalid empty topic
        message_type="invalid_type",  # Invalid message type
        data=b"",  # Empty data
        timestamp=-1,  # Invalid timestamp
        source_node=""  # Invalid node name
    )
    
    print(f"Invalid message test: {'PASS' if not is_valid else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")


async def main():
    """Main demonstration function."""
    print("ROS Data Storage System - rosbag-like Demo")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Create sample data
    messages = await create_rosbag_like_data()
    
    # Demonstrate recording
    session_id = await demonstrate_recording(messages)
    
    if session_id:
        # Demonstrate playback
        await demonstrate_playback(session_id)
        
        # Demonstrate search
        await demonstrate_search()
    
    # Demonstrate compression
    await demonstrate_compression()
    
    # Demonstrate validation
    await demonstrate_validation()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nYou can now use the command-line interface:")
    print("  python -m data.main record --name 'my_session'")
    print("  python -m data.main play --session-id 1")
    print("  python -m data.main list")
    print("  python -m data.main search --topics '/cmd_vel'")


if __name__ == "__main__":
    asyncio.run(main()) 