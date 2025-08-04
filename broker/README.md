# DeepROS MQTT Broker

A lightweight, high-performance MQTT broker with ROS (Robot Operating System) integration support, built with Python and asyncio.

## Features

- **MQTT 3.1.1 Protocol Support**: Full MQTT protocol implementation
- **WebSocket Support**: MQTT over WebSocket for web applications
- **ROS Integration**: Specialized support for ROS domain management
- **Authentication**: Username/password authentication
- **TLS/SSL Support**: Secure connections with certificates
- **Retained Messages**: Support for MQTT retained messages
- **Wildcard Subscriptions**: Support for + and # wildcards
- **QoS Levels**: Support for QoS 0, 1, and 2
- **Session Management**: Persistent sessions and clean session support
- **Statistics and Monitoring**: Built-in statistics and monitoring
- **High Performance**: Asynchronous I/O with asyncio

## Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager

### Install Dependencies

```bash
# Install broker dependencies
uv add asyncio-mqtt paho-mqtt websockets
```

### Configuration

Copy the environment example and configure your settings:

```bash
cp env.example .env
```

Edit `.env` file with your broker configuration:

```env
# MQTT Broker Configuration
BROKER_MQTT_HOST=0.0.0.0
BROKER_MQTT_PORT=1883
BROKER_WEBSOCKET_ENABLED=true
BROKER_WEBSOCKET_PORT=9001
BROKER_ENABLE_AUTH=false
BROKER_LOG_LEVEL=INFO
```

## Usage

### Starting the Broker

```bash
# Start with default settings
python -m Broker.main

# Start with custom port
python -m Broker.main --mqtt-port 1884

# Start with authentication enabled
python -m Broker.main --enable-auth

# Start with debug logging
python -m Broker.main --log-level DEBUG
```

### Command Line Options

```bash
python -m Broker.main [options]

Options:
    -h, --help          Show help message
    -v, --version       Show version information
    --mqtt-host HOST    MQTT server host (default: 0.0.0.0)
    --mqtt-port PORT    MQTT server port (default: 1883)
    --ws-host HOST      WebSocket server host (default: 0.0.0.0)
    --ws-port PORT      WebSocket server port (default: 9001)
    --enable-auth       Enable authentication
    --enable-tls        Enable TLS/SSL
    --log-level LEVEL   Set log level (DEBUG, INFO, WARNING, ERROR)
    --log-file FILE     Log to file
```

### Running Tests

```bash
# Run the test suite
python -m Broker.test_broker
```

## API Reference

### Core Classes

#### MQTTBroker

The main broker class that orchestrates all broker functionality.

```python
from Broker.core.broker import MQTTBroker

# Create broker instance
broker = MQTTBroker()

# Start the broker
await broker.start()

# Publish a message
subscribers = broker.publish("test/topic", b"Hello World", qos=1)

# Subscribe a client
broker.subscribe("client1", "test/topic", qos=1)

# Get statistics
stats = broker.get_statistics()
```

#### SessionManager

Manages client connections and sessions.

```python
from Broker.core.session_manager import SessionManager

session_manager = SessionManager()

# Create client
client = session_manager.create_client("client1", username="user1")

# Connect client
session_manager.connect_client("client1", transport, protocol)

# Get client info
info = session_manager.get_client_info("client1")
```

#### TopicManager

Manages topics, subscriptions, and message routing.

```python
from Broker.core.topic_manager import TopicManager

topic_manager = TopicManager()

# Subscribe to topic
topic_manager.subscribe("client1", "sensors/temperature", qos=1)

# Publish message
subscribers = topic_manager.publish_message(message)

# Get topic info
info = topic_manager.get_topic_info("sensors/temperature")
```

### Models

#### Message

Represents an MQTT message.

```python
from Broker.models.message import Message

message = Message(
    topic="sensors/temperature",
    payload=b"25.5",
    qos=1,
    retain=False,
    client_id="publisher1"
)

# Convert to dictionary
data = message.to_dict()

# Create from dictionary
message = Message.from_dict(data)
```

#### Client

Represents an MQTT client connection.

```python
from Broker.models.client import Client

client = Client(
    client_id="client1",
    username="user1",
    clean_session=True,
    keepalive=60
)

# Check if client is idle
is_idle = client.is_idle(timeout_seconds=300)
```

#### Topic

Represents an MQTT topic with subscribers and retained messages.

```python
from Broker.models.topic import Topic

topic = Topic(name="sensors/temperature")

# Add subscriber
topic.add_subscriber("client1", qos=1)

# Set retained message
topic.set_retained_message(message)

# Get subscribers
subscribers = topic.get_subscribers_list()
```

## ROS Integration

The broker includes special support for ROS (Robot Operating System) integration:

### ROS Topic Structure

ROS topics follow the pattern: `ros/{domain}/{node}/{message_type}`

Example:
- `ros/autonomous_vehicle/sensor_fusion/sensor_data`
- `ros/autonomous_vehicle/path_planner/path_update`

### ROS Message Handling

```python
# ROS messages are automatically parsed for domain, node, and message type
message = Message(topic="ros/autonomous_vehicle/sensor_fusion/sensor_data")
message.extract_ros_info()

print(message.ros_domain)  # "autonomous_vehicle"
print(message.ros_node)    # "sensor_fusion"
print(message.ros_message_type)  # "sensor_data"
```

### ROS Integration Configuration

```env
# Enable ROS integration
BROKER_ENABLE_ROS_INTEGRATION=true

# Set ROS domain prefix
BROKER_ROS_DOMAIN_PREFIX=ros/
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BROKER_MQTT_HOST` | `0.0.0.0` | MQTT server host |
| `BROKER_MQTT_PORT` | `1883` | MQTT server port |
| `BROKER_MQTT_KEEPALIVE` | `60` | Keepalive interval in seconds |
| `BROKER_MQTT_MAX_CONNECTIONS` | `1000` | Maximum number of connections |
| `BROKER_WEBSOCKET_HOST` | `0.0.0.0` | WebSocket server host |
| `BROKER_WEBSOCKET_PORT` | `9001` | WebSocket server port |
| `BROKER_WEBSOCKET_ENABLED` | `true` | Enable WebSocket support |
| `BROKER_ENABLE_AUTH` | `false` | Enable authentication |
| `BROKER_USERNAME` | `admin` | Default username |
| `BROKER_PASSWORD` | `password` | Default password |
| `BROKER_ENABLE_TLS` | `false` | Enable TLS/SSL |
| `BROKER_TLS_CERT_FILE` | - | TLS certificate file path |
| `BROKER_TLS_KEY_FILE` | - | TLS private key file path |
| `BROKER_TLS_CA_FILE` | - | TLS CA certificate file path |
| `BROKER_MAX_MESSAGE_SIZE` | `268435455` | Maximum message size (256MB) |
| `BROKER_MAX_INFLIGHT_MESSAGES` | `20` | Maximum inflight messages per client |
| `BROKER_MAX_QUEUED_MESSAGES` | `100` | Maximum queued messages per client |
| `BROKER_ROS_DOMAIN_PREFIX` | `ros/` | ROS topic prefix |
| `BROKER_ENABLE_ROS_INTEGRATION` | `true` | Enable ROS integration |
| `BROKER_LOG_LEVEL` | `INFO` | Log level |
| `BROKER_LOG_FILE` | - | Log file path |

## Security

### Authentication

Enable authentication by setting `BROKER_ENABLE_AUTH=true` and configuring username/password:

```env
BROKER_ENABLE_AUTH=true
BROKER_USERNAME=myuser
BROKER_PASSWORD=mypassword
```

### TLS/SSL

Enable TLS/SSL for secure connections:

```env
BROKER_ENABLE_TLS=true
BROKER_TLS_CERT_FILE=/path/to/cert.pem
BROKER_TLS_KEY_FILE=/path/to/key.pem
BROKER_TLS_CA_FILE=/path/to/ca.pem
```

## Monitoring and Statistics

The broker provides comprehensive statistics:

```python
stats = broker.get_statistics()

# Broker status
print(stats['broker']['running'])
print(stats['broker']['mqtt_server_active'])

# Session statistics
print(stats['session']['total_clients'])
print(stats['session']['connected_clients'])
print(stats['session']['total_subscriptions'])

# Topic statistics
print(stats['topics']['total_topics'])
print(stats['topics']['total_subscribers'])
print(stats['topics']['total_retained_messages'])
```

## Examples

### Basic Publisher/Subscriber

```python
import asyncio
from asyncio_mqtt import Client

async def publisher():
    client = Client("publisher")
    await client.connect("localhost", 1883)
    
    await client.publish("test/topic", "Hello MQTT!")
    await client.disconnect()

async def subscriber():
    client = Client("subscriber")
    await client.connect("localhost", 1883)
    
    await client.subscribe("test/topic")
    async with client.messages() as messages:
        async for message in messages:
            print(f"Received: {message.payload.decode()}")
            break
    
    await client.disconnect()

# Run both
asyncio.run(asyncio.gather(publisher(), subscriber()))
```

### ROS Integration Example

```python
import asyncio
import json
from asyncio_mqtt import Client

async def ros_publisher():
    client = Client("ros_publisher")
    await client.connect("localhost", 1883)
    
    # Publish ROS sensor data
    sensor_data = {
        "timestamp": "2024-01-01T12:00:00Z",
        "temperature": 25.5,
        "humidity": 60.2
    }
    
    topic = "ros/autonomous_vehicle/sensor_fusion/sensor_data"
    payload = json.dumps(sensor_data).encode()
    
    await client.publish(topic, payload)
    await client.disconnect()

asyncio.run(ros_publisher())
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port using `--mqtt-port` or `BROKER_MQTT_PORT`
2. **Permission denied**: Run with appropriate permissions or change the host to `127.0.0.1`
3. **WebSocket not working**: Ensure `websockets` package is installed
4. **Authentication failing**: Check username/password configuration

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python -m Broker.main --log-level DEBUG
```

### Log Files

Configure log file output:

```bash
python -m Broker.main --log-file broker.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 