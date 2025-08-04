#!/usr/bin/env python3
"""
MQTT Broker Test Script

This script demonstrates the MQTT broker functionality by creating
sample publishers and subscribers.
"""

import asyncio
import json
import logging
from asyncio_mqtt import Client as MQTTClient
from .core.broker import MQTTBroker
from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_publisher(broker, topic: str, messages: list):
    """Test publisher that sends messages to a topic"""
    try:
        # Create MQTT client
        client = MQTTClient("test_publisher")
        await client.connect("localhost", settings.mqtt_port)
        
        logger.info(f"Publisher connected, sending {len(messages)} messages to {topic}")
        
        # Send messages
        for i, message in enumerate(messages):
            payload = json.dumps(message).encode('utf-8')
            await client.publish(topic, payload)
            logger.info(f"Published message {i+1}: {message}")
            await asyncio.sleep(1)
        
        # Disconnect
        await client.disconnect()
        logger.info("Publisher disconnected")
        
    except Exception as e:
        logger.error(f"Publisher error: {e}")


async def test_subscriber(broker, topic: str, client_id: str):
    """Test subscriber that receives messages from a topic"""
    try:
        # Create MQTT client
        client = MQTTClient(client_id)
        await client.connect("localhost", settings.mqtt_port)
        
        logger.info(f"Subscriber {client_id} connected, subscribing to {topic}")
        
        # Subscribe to topic
        await client.subscribe(topic)
        
        # Receive messages
        async with client.messages() as messages:
            async for message in messages:
                try:
                    payload = json.loads(message.payload.decode('utf-8'))
                    logger.info(f"Subscriber {client_id} received: {payload}")
                except json.JSONDecodeError:
                    logger.info(f"Subscriber {client_id} received: {message.payload.decode('utf-8')}")
        
    except Exception as e:
        logger.error(f"Subscriber {client_id} error: {e}")


async def test_ros_integration(broker):
    """Test ROS-specific functionality"""
    try:
        # Create ROS domain publisher
        ros_client = MQTTClient("ros_publisher")
        await ros_client.connect("localhost", settings.mqtt_port)
        
        # Publish ROS messages
        ros_messages = [
            {
                "domain": "autonomous_vehicle",
                "node": "sensor_fusion",
                "message_type": "sensor_data",
                "data": {
                    "timestamp": "2024-01-01T12:00:00Z",
                    "sensors": ["lidar", "camera", "gps"],
                    "values": [1.5, 2.3, 3.7]
                }
            },
            {
                "domain": "autonomous_vehicle",
                "node": "path_planner",
                "message_type": "path_update",
                "data": {
                    "timestamp": "2024-01-01T12:00:01Z",
                    "waypoints": [[10, 20], [15, 25], [20, 30]],
                    "speed": 5.0
                }
            }
        ]
        
        for message in ros_messages:
            topic = f"ros/{message['domain']}/{message['node']}/{message['message_type']}"
            payload = json.dumps(message['data']).encode('utf-8')
            await ros_client.publish(topic, payload)
            logger.info(f"Published ROS message to {topic}")
            await asyncio.sleep(1)
        
        await ros_client.disconnect()
        
    except Exception as e:
        logger.error(f"ROS integration test error: {e}")


async def run_tests():
    """Run all broker tests"""
    # Create and start broker
    broker = MQTTBroker()
    await broker.start()
    
    try:
        # Test data
        test_messages = [
            {"id": 1, "text": "Hello MQTT!", "timestamp": "2024-01-01T12:00:00Z"},
            {"id": 2, "text": "This is a test message", "timestamp": "2024-01-01T12:00:01Z"},
            {"id": 3, "text": "MQTT broker is working!", "timestamp": "2024-01-01T12:00:02Z"},
        ]
        
        # Start subscribers
        subscriber1 = asyncio.create_task(
            test_subscriber(broker, "test/topic", "subscriber1")
        )
        subscriber2 = asyncio.create_task(
            test_subscriber(broker, "test/topic", "subscriber2")
        )
        wildcard_subscriber = asyncio.create_task(
            test_subscriber(broker, "test/#", "wildcard_subscriber")
        )
        
        # Wait a bit for subscribers to connect
        await asyncio.sleep(2)
        
        # Start publisher
        publisher = asyncio.create_task(
            test_publisher(broker, "test/topic", test_messages)
        )
        
        # Wait for publisher to finish
        await publisher
        
        # Test ROS integration
        await asyncio.sleep(1)
        ros_test = asyncio.create_task(test_ros_integration(broker))
        await ros_test
        
        # Wait a bit more for messages to be processed
        await asyncio.sleep(3)
        
        # Print broker statistics
        stats = broker.get_statistics()
        logger.info("Broker Statistics:")
        logger.info(json.dumps(stats, indent=2))
        
        # Cancel subscribers
        subscriber1.cancel()
        subscriber2.cancel()
        wildcard_subscriber.cancel()
        
        # Wait for cleanup
        await asyncio.sleep(1)
        
    finally:
        # Stop broker
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(run_tests()) 