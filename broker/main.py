#!/usr/bin/env python3
"""
MQTT Broker - Main Entry Point

This module provides the main entry point for the MQTT broker.
It handles command-line arguments, logging setup, and broker startup.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from .core.broker import MQTTBroker
from .config import settings


def setup_logging():
    """Set up logging configuration"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Set up file handler if log file is specified
    handlers = [console_handler]
    if settings.log_file:
        try:
            file_handler = logging.FileHandler(settings.log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file {settings.log_file}: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_banner():
    """Print the broker banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    DeepROS MQTT Broker                       ║
║                                                              ║
║  A lightweight MQTT broker with ROS integration support     ║
║                                                              ║
║  MQTT Server:    {}:{}                              ║
║  WebSocket:      {}:{}                              ║
║  Authentication: {}                                    ║
║  TLS/SSL:        {}                                    ║
╚══════════════════════════════════════════════════════════════╝
""".format(
        settings.mqtt_host,
        settings.mqtt_port,
        settings.websocket_host if settings.websocket_enabled else "Disabled",
        settings.websocket_port if settings.websocket_enabled else "",
        "Enabled" if settings.enable_auth else "Disabled",
        "Enabled" if settings.enable_tls else "Disabled"
    )
    print(banner)


def print_usage():
    """Print usage information"""
    usage = """
Usage: python -m Broker.main [options]

Options:
    -h, --help          Show this help message
    -v, --version       Show version information
    -c, --config FILE   Load configuration from file
    --mqtt-host HOST    MQTT server host (default: 0.0.0.0)
    --mqtt-port PORT    MQTT server port (default: 1883)
    --ws-host HOST      WebSocket server host (default: 0.0.0.0)
    --ws-port PORT      WebSocket server port (default: 9001)
    --enable-auth       Enable authentication
    --enable-tls        Enable TLS/SSL
    --log-level LEVEL   Set log level (DEBUG, INFO, WARNING, ERROR)
    --log-file FILE     Log to file

Environment Variables:
    BROKER_MQTT_HOST, BROKER_MQTT_PORT
    BROKER_WEBSOCKET_HOST, BROKER_WEBSOCKET_PORT
    BROKER_ENABLE_AUTH, BROKER_USERNAME, BROKER_PASSWORD
    BROKER_ENABLE_TLS, BROKER_TLS_CERT_FILE, BROKER_TLS_KEY_FILE
    BROKER_LOG_LEVEL, BROKER_LOG_FILE

Examples:
    python -m Broker.main
    python -m Broker.main --mqtt-port 1884 --enable-auth
    python -m Broker.main --log-level DEBUG --log-file broker.log
"""
    print(usage)


def print_version():
    """Print version information"""
    from . import __version__
    print(f"DeepROS MQTT Broker v{__version__}")


def parse_arguments():
    """Parse command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DeepROS MQTT Broker",
        add_help=False
    )
    
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    parser.add_argument('-v', '--version', action='store_true', help='Show version information')
    parser.add_argument('-c', '--config', help='Configuration file path')
    parser.add_argument('--mqtt-host', help='MQTT server host')
    parser.add_argument('--mqtt-port', type=int, help='MQTT server port')
    parser.add_argument('--ws-host', help='WebSocket server host')
    parser.add_argument('--ws-port', type=int, help='WebSocket server port')
    parser.add_argument('--enable-auth', action='store_true', help='Enable authentication')
    parser.add_argument('--enable-tls', action='store_true', help='Enable TLS/SSL')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Log level')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Handle help and version
    if args.help:
        print_usage()
        sys.exit(0)
    
    if args.version:
        print_version()
        sys.exit(0)
    
    # Apply command line arguments to settings
    if args.mqtt_host:
        settings.mqtt_host = args.mqtt_host
    if args.mqtt_port:
        settings.mqtt_port = args.mqtt_port
    if args.ws_host:
        settings.websocket_host = args.ws_host
    if args.ws_port:
        settings.websocket_port = args.ws_port
    if args.enable_auth:
        settings.enable_auth = True
    if args.enable_tls:
        settings.enable_tls = True
    if args.log_level:
        settings.log_level = args.log_level
    if args.log_file:
        settings.log_file = args.log_file
    
    return args


async def main():
    """Main function"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set up logging
        setup_logging()
        
        # Print banner
        print_banner()
        
        # Create and start broker
        broker = MQTTBroker()
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            logger = logging.getLogger(__name__)
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(broker.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the broker
        await broker.run_forever()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 