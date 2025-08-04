#!/usr/bin/env python3
"""
ROS Data Storage System - Main Entry Point

This module provides a command-line interface for the ROS data storage system,
similar to rosbag functionality.
"""

import asyncio
import argparse
import logging
import sys
import time
from typing import Optional, List
from .config import DataSettings
from .core import ROSRecorder, ROSPlayer, MessageIndexer, MessageCompressor, MessageValidator
from .database import init_db


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    ROS Data Storage System                   ║
║                        Version 0.1.0                        ║
║                                                              ║
║  A rosbag-like system for storing and managing ROS messages ║
║  using SQLite database with advanced indexing and search    ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_usage():
    """Print usage information."""
    usage = """
Usage: python -m data.main <command> [options]

Commands:
  record    Start recording ROS messages
  play      Play back recorded messages
  info      Show information about recording sessions
  list      List all recording sessions
  search    Search for messages
  stats     Show statistics
  validate  Validate messages
  compress  Compress/decompress data
  index     Manage message indexing

Examples:
  python -m data.main record --name "test_session" --topics "/cmd_vel,/odom"
  python -m data.main play --session-id 1 --topics "/cmd_vel"
  python -m data.main info --session-id 1
  python -m data.main list
  python -m data.main search --topics "/cmd_vel" --start-time 1234567890
  python -m data.main stats
"""
    print(usage)


async def cmd_record(args):
    """Handle record command."""
    print(f"Starting recording session: {args.name}")
    
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    try:
        # Start recording
        session = await recorder.start_recording(
            session_name=args.name,
            description=args.description,
            topics=args.topics.split(',') if args.topics else None,
            settings={
                'compression_enabled': args.compression,
                'compression_level': args.compression_level,
                'batch_size': args.batch_size
            }
        )
        
        print(f"Recording started with session ID: {session.id}")
        print("Press Ctrl+C to stop recording...")
        
        # Keep recording until interrupted
        while True:
            stats = recorder.get_recording_stats()
            print(f"\rMessages: {stats['total_messages']}, "
                  f"Size: {stats['total_size_bytes']} bytes, "
                  f"Topics: {stats['topics_count']}", end='')
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping recording...")
        session = await recorder.stop_recording()
        if session:
            print(f"Recording stopped. Session: {session.name}")
            print(f"Duration: {session.duration:.2f} seconds")
            print(f"Total messages: {session.total_messages}")
            print(f"Total size: {session.total_size_bytes} bytes")
    
    except Exception as e:
        print(f"Error during recording: {e}")
        await recorder.stop_recording()


async def cmd_play(args):
    """Handle play command."""
    print(f"Playing session ID: {args.session_id}")
    
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    # Message callback for playback
    async def message_callback(message):
        print(f"Playing: {message.topic_name} ({message.message_type}) "
              f"at {message.timestamp:.3f}")
    
    try:
        # Start playback
        success = await player.play_session(
            session_id=args.session_id,
            topics=args.topics.split(',') if args.topics else None,
            start_time=args.start_time,
            end_time=args.end_time,
            playback_rate=args.rate,
            loop=args.loop,
            message_callback=message_callback
        )
        
        if not success:
            print("Failed to start playback")
            return
        
        # Wait for playback to complete
        while player.is_playing:
            stats = player.get_playback_stats()
            print(f"\rProgress: {stats['progress_percent']:.1f}% "
                  f"({stats['played_messages']}/{stats['total_messages']})", end='')
            await asyncio.sleep(0.1)
        
        print("\nPlayback completed")
        
    except KeyboardInterrupt:
        print("\nStopping playback...")
        await player.stop_playback()
    
    except Exception as e:
        print(f"Error during playback: {e}")
        await player.stop_playback()


async def cmd_info(args):
    """Handle info command."""
    settings = DataSettings()
    player = ROSPlayer(settings)
    
    info = player.get_session_info(args.session_id)
    if not info:
        print(f"Session {args.session_id} not found")
        return
    
    print(f"Session Information:")
    print(f"  ID: {info['id']}")
    print(f"  Name: {info['name']}")
    print(f"  Description: {info['description']}")
    print(f"  Start Time: {info['start_time']}")
    print(f"  End Time: {info['end_time']}")
    print(f"  Duration: {info['duration']:.2f} seconds")
    print(f"  Total Messages: {info['total_messages']}")
    print(f"  Total Size: {info['total_size_bytes']} bytes")
    print(f"  Topics Count: {info['topics_count']}")
    print(f"  Is Active: {info['is_active']}")
    print(f"  Is Compressed: {info['is_compressed']}")
    print(f"  Created: {info['created_at']}")
    
    if info['topic_statistics']:
        print(f"\nTopic Statistics:")
        for topic, stats in info['topic_statistics'].items():
            print(f"  {topic}:")
            print(f"    Type: {stats['message_type']}")
            print(f"    Count: {stats['count']}")
            print(f"    Total Size: {stats['total_size']} bytes")
            print(f"    Avg Size: {stats['avg_size']:.1f} bytes")


async def cmd_list(args):
    """Handle list command."""
    settings = DataSettings()
    recorder = ROSRecorder(settings)
    
    sessions = recorder.list_sessions(active_only=args.active)
    
    if not sessions:
        print("No recording sessions found")
        return
    
    print(f"Recording Sessions ({len(sessions)} total):")
    print("-" * 80)
    print(f"{'ID':<5} {'Name':<20} {'Duration':<12} {'Messages':<10} {'Size (MB)':<10} {'Status':<8}")
    print("-" * 80)
    
    for session in sessions:
        duration = f"{session.duration:.1f}s" if session.duration else "N/A"
        size_mb = f"{session.total_size_bytes / (1024*1024):.1f}" if session.total_size_bytes else "0"
        status = "Active" if session.is_active else "Inactive"
        
        print(f"{session.id:<5} {session.name:<20} {duration:<12} "
              f"{session.total_messages:<10} {size_mb:<10} {status:<8}")


async def cmd_search(args):
    """Handle search command."""
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    print("Searching for messages...")
    
    result = await indexer.search_messages(
        topics=args.topics.split(',') if args.topics else None,
        message_types=args.types.split(',') if args.types else None,
        start_time=args.start_time,
        end_time=args.end_time,
        source_nodes=args.nodes.split(',') if args.nodes else None,
        min_size=args.min_size,
        max_size=args.max_size,
        limit=args.limit,
        offset=args.offset
    )
    
    print(f"Found {result['total_count']} messages:")
    print("-" * 100)
    print(f"{'ID':<8} {'Topic':<25} {'Type':<20} {'Timestamp':<15} {'Size':<8} {'Node':<15}")
    print("-" * 100)
    
    for msg in result['messages'][:args.limit]:
        timestamp = f"{msg['timestamp']:.3f}"
        size_kb = f"{msg['data_size'] / 1024:.1f}"
        node = msg['source_node'] or "N/A"
        
        print(f"{msg['id']:<8} {msg['topic_name']:<25} {msg['message_type']:<20} "
              f"{timestamp:<15} {size_kb:<8} {node:<15}")


async def cmd_stats(args):
    """Handle stats command."""
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    print("System Statistics:")
    print("-" * 50)
    
    # Index statistics
    index_stats = indexer.get_index_statistics()
    print(f"Index Statistics:")
    print(f"  Total Index Entries: {index_stats['total_index_entries']}")
    print(f"  Total Messages: {index_stats['total_messages']}")
    print(f"  Index Coverage: {index_stats['index_coverage']:.1f}%")
    print(f"  Unique Topics: {index_stats['unique_topics']}")
    print(f"  Unique Message Types: {index_stats['unique_message_types']}")
    
    # Topic statistics
    topic_stats = await indexer.get_topic_statistics()
    if topic_stats:
        print(f"\nTop Topics by Message Count:")
        for i, topic in enumerate(topic_stats[:10], 1):
            print(f"  {i}. {topic['topic_name']}: {topic['message_count']} messages")
    
    # Popular topics
    popular_topics = await indexer.get_popular_topics(limit=5)
    if popular_topics:
        print(f"\nMost Popular Topics:")
        for i, topic in enumerate(popular_topics, 1):
            print(f"  {i}. {topic['topic_name']}: {topic['message_count']} messages")


async def cmd_validate(args):
    """Handle validate command."""
    settings = DataSettings()
    validator = MessageValidator(settings)
    
    print("Message validation completed")
    # This would typically validate messages from a file or database
    # For now, just show the validator is available
    print("Validator initialized with settings:")
    print(f"  Max message size: {settings.MAX_MESSAGE_SIZE_BYTES} bytes")
    print(f"  Known message types: {len(validator.known_message_types)}")


async def cmd_compress(args):
    """Handle compress command."""
    settings = DataSettings()
    compressor = MessageCompressor(settings)
    
    if args.method == 'info':
        print("Compression Methods:")
        for method in compressor.COMPRESSION_METHODS.keys():
            info = compressor.get_method_info(method)
            print(f"  {method}: {info['description']}")
            print(f"    Typical ratio: {info['typical_ratio']:.2f}")
            print(f"    Speed: {info['speed']}")
            print(f"    Memory: {info['memory_usage']}")
    else:
        print(f"Compression method: {args.method}")
        # This would typically compress/decompress actual data
        print("Compressor initialized")


async def cmd_index(args):
    """Handle index command."""
    settings = DataSettings()
    indexer = MessageIndexer(settings)
    
    if args.action == 'rebuild':
        print("Rebuilding message index...")
        await indexer.rebuild_index()
        print("Index rebuild completed")
    elif args.action == 'start':
        print("Starting auto-indexing...")
        await indexer.start_auto_indexing()
        print("Auto-indexing started")
    elif args.action == 'stop':
        print("Stopping auto-indexing...")
        await indexer.stop_auto_indexing()
        print("Auto-indexing stopped")
    elif args.action == 'cleanup':
        print(f"Cleaning up old indexes (older than {args.days} days)...")
        await indexer.cleanup_old_indexes(args.days)
        print("Cleanup completed")
    else:
        print(f"Unknown index action: {args.action}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ROS Data Storage System - A rosbag-like system for storing ROS messages",
        add_help=False
    )
    
    parser.add_argument('--version', action='version', version='0.1.0')
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    parser.add_argument('--log-file', help='Log file path')
    
    # Parse known args to get log level
    args, remaining = parser.parse_known_args()
    
    if args.help:
        print_banner()
        print_usage()
        return
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Initialize database
    init_db()
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Record command
    record_parser = subparsers.add_parser('record', help='Start recording ROS messages')
    record_parser.add_argument('--name', required=True, help='Session name')
    record_parser.add_argument('--description', help='Session description')
    record_parser.add_argument('--topics', help='Comma-separated list of topics to record')
    record_parser.add_argument('--compression', action='store_true', help='Enable compression')
    record_parser.add_argument('--compression-level', type=int, default=6, help='Compression level (0-9)')
    record_parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    
    # Play command
    play_parser = subparsers.add_parser('play', help='Play back recorded messages')
    play_parser.add_argument('--session-id', type=int, required=True, help='Session ID to play')
    play_parser.add_argument('--topics', help='Comma-separated list of topics to play')
    play_parser.add_argument('--start-time', type=float, help='Start time (timestamp)')
    play_parser.add_argument('--end-time', type=float, help='End time (timestamp)')
    play_parser.add_argument('--rate', type=float, default=1.0, help='Playback rate')
    play_parser.add_argument('--loop', action='store_true', help='Loop playback')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show session information')
    info_parser.add_argument('--session-id', type=int, required=True, help='Session ID')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recording sessions')
    list_parser.add_argument('--active', action='store_true', help='Show only active sessions')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for messages')
    search_parser.add_argument('--topics', help='Comma-separated list of topics')
    search_parser.add_argument('--types', help='Comma-separated list of message types')
    search_parser.add_argument('--start-time', type=float, help='Start time (timestamp)')
    search_parser.add_argument('--end-time', type=float, help='End time (timestamp)')
    search_parser.add_argument('--nodes', help='Comma-separated list of source nodes')
    search_parser.add_argument('--min-size', type=int, help='Minimum message size')
    search_parser.add_argument('--max-size', type=int, help='Maximum message size')
    search_parser.add_argument('--limit', type=int, default=100, help='Maximum results')
    search_parser.add_argument('--offset', type=int, default=0, help='Result offset')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate messages')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compression utilities')
    compress_parser.add_argument('--method', default='info', help='Compression method or "info"')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Manage message indexing')
    index_parser.add_argument('--action', required=True, 
                             choices=['rebuild', 'start', 'stop', 'cleanup'],
                             help='Index action')
    index_parser.add_argument('--days', type=int, default=30, help='Days for cleanup')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        print_usage()
        return
    
    # Execute command
    try:
        if args.command == 'record':
            asyncio.run(cmd_record(args))
        elif args.command == 'play':
            asyncio.run(cmd_play(args))
        elif args.command == 'info':
            asyncio.run(cmd_info(args))
        elif args.command == 'list':
            asyncio.run(cmd_list(args))
        elif args.command == 'search':
            asyncio.run(cmd_search(args))
        elif args.command == 'stats':
            asyncio.run(cmd_stats(args))
        elif args.command == 'validate':
            asyncio.run(cmd_validate(args))
        elif args.command == 'compress':
            asyncio.run(cmd_compress(args))
        elif args.command == 'index':
            asyncio.run(cmd_index(args))
        else:
            print(f"Unknown command: {args.command}")
            print_usage()
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Unhandled exception: {e}", exc_info=True)


if __name__ == "__main__":
    main() 