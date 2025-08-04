import asyncio
import logging
import ssl
from typing import Optional, Dict, Any
from ..config import settings
from .session_manager import SessionManager
from .topic_manager import TopicManager
from .protocol import MQTTProtocol
from ..models.message import Message

logger = logging.getLogger(__name__)


class MQTTBroker:
    """Main MQTT Broker implementation"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.topic_manager = TopicManager()
        self.mqtt_server: Optional[asyncio.Server] = None
        self.websocket_server: Optional[asyncio.Server] = None
        self.running = False
        
        # Set up message routing
        self.topic_manager.add_message_handler(self._handle_message)
    
    async def start(self):
        """Start the MQTT broker"""
        if self.running:
            logger.warning("Broker is already running")
            return
        
        try:
            # Start session manager
            await self.session_manager.start()
            
            # Start MQTT server
            await self._start_mqtt_server()
            
            # Start WebSocket server if enabled
            if settings.websocket_enabled:
                await self._start_websocket_server()
            
            self.running = True
            logger.info("MQTT Broker started successfully")
            logger.info(f"MQTT server listening on {settings.mqtt_host}:{settings.mqtt_port}")
            if settings.websocket_enabled:
                logger.info(f"WebSocket server listening on {settings.websocket_host}:{settings.websocket_port}")
            
        except Exception as e:
            logger.error(f"Failed to start MQTT broker: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the MQTT broker"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop servers
        if self.mqtt_server:
            self.mqtt_server.close()
            await self.mqtt_server.wait_closed()
        
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # Stop session manager
        await self.session_manager.stop()
        
        logger.info("MQTT Broker stopped")
    
    async def _start_mqtt_server(self):
        """Start the MQTT TCP server"""
        try:
            # Create SSL context if TLS is enabled
            ssl_context = None
            if settings.enable_tls:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                if settings.tls_cert_file and settings.tls_key_file:
                    ssl_context.load_cert_chain(settings.tls_cert_file, settings.tls_key_file)
                if settings.tls_ca_file:
                    ssl_context.load_verify_locations(settings.tls_ca_file)
            
            # Create server
            self.mqtt_server = await asyncio.start_server(
                self._mqtt_connection_handler,
                settings.mqtt_host,
                settings.mqtt_port,
                ssl=ssl_context,
                limit=settings.max_message_size
            )
            
        except Exception as e:
            logger.error(f"Failed to start MQTT server: {e}")
            raise
    
    async def _start_websocket_server(self):
        """Start the WebSocket server"""
        try:
            # Import websockets here to avoid dependency issues
            import websockets
            
            async def websocket_handler(websocket, path):
                await self._handle_websocket_connection(websocket, path)
            
            self.websocket_server = await websockets.serve(
                websocket_handler,
                settings.websocket_host,
                settings.websocket_port
            )
            
        except ImportError:
            logger.warning("WebSocket support not available. Install websockets package.")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    def _mqtt_connection_handler(self, reader, writer):
        """Handle new MQTT TCP connections"""
        try:
            transport = writer.transport
            protocol = MQTTProtocol(self)
            protocol.connection_made(transport)
            
            # Set up data handling
            async def handle_data():
                try:
                    while True:
                        data = await reader.read(1024)
                        if not data:
                            break
                        protocol.data_received(data)
                except Exception as e:
                    logger.error(f"Error handling MQTT data: {e}")
                finally:
                    writer.close()
                    await writer.wait_closed()
            
            # Start data handling task
            asyncio.create_task(handle_data())
            
        except Exception as e:
            logger.error(f"Error handling MQTT connection: {e}")
            writer.close()
    
    async def _handle_websocket_connection(self, websocket, path):
        """Handle WebSocket connections"""
        try:
            # Create a simple WebSocket to MQTT bridge
            # This is a basic implementation - in production you'd want more robust handling
            async for message in websocket:
                try:
                    # Parse WebSocket message as MQTT
                    # This is simplified - you'd need proper MQTT over WebSocket handling
                    logger.debug(f"WebSocket message: {message}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
    
    def _handle_message(self, message: Message):
        """Handle incoming messages"""
        try:
            # Route message to subscribers
            subscribers = self.topic_manager.publish_message(message)
            
            # Send message to each subscriber
            for client_id in subscribers:
                client = self.session_manager.get_client(client_id)
                if client and client.connected and client.protocol:
                    # Get QoS for this client
                    topic = self.topic_manager.get_or_create_topic(message.topic)
                    qos = topic.get_subscriber_qos(client_id)
                    
                    # Send message
                    client.protocol.send_message(message, qos)
            
            logger.debug(f"Message routed to {len(subscribers)} subscribers")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def publish(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False) -> int:
        """Publish a message to a topic"""
        try:
            message = Message(
                topic=topic,
                payload=payload,
                qos=qos,
                retain=retain,
                client_id="system"
            )
            
            subscribers = self.topic_manager.publish_message(message)
            return len(subscribers)
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return 0
    
    def subscribe(self, client_id: str, topic: str, qos: int = 0) -> bool:
        """Subscribe a client to a topic"""
        return self.topic_manager.subscribe(client_id, topic, qos)
    
    def unsubscribe(self, client_id: str, topic: str) -> bool:
        """Unsubscribe a client from a topic"""
        return self.topic_manager.unsubscribe(client_id, topic)
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a client"""
        return self.session_manager.get_client_info(client_id)
    
    def get_all_clients_info(self) -> list:
        """Get information about all clients"""
        return self.session_manager.get_all_clients_info()
    
    def get_topic_info(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a topic"""
        return self.topic_manager.get_topic_info(topic_name)
    
    def get_all_topics_info(self) -> list:
        """Get information about all topics"""
        return self.topic_manager.get_all_topics()
    
    def get_client_subscriptions(self, client_id: str) -> list:
        """Get all topics a client is subscribed to"""
        return self.topic_manager.get_client_subscriptions(client_id)
    
    def disconnect_client(self, client_id: str, reason: str = "Admin disconnect"):
        """Disconnect a client"""
        self.session_manager.disconnect_client(client_id, reason)
    
    def remove_client(self, client_id: str):
        """Remove a client session"""
        # Remove subscriptions
        self.topic_manager.remove_client_subscriptions(client_id)
        
        # Remove client
        self.session_manager.remove_client(client_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get broker statistics"""
        session_stats = self.session_manager.get_statistics()
        topic_stats = self.topic_manager.get_statistics()
        
        return {
            'broker': {
                'running': self.running,
                'mqtt_server_active': self.mqtt_server is not None,
                'websocket_server_active': self.websocket_server is not None,
            },
            'session': session_stats,
            'topics': topic_stats,
        }
    
    def cleanup(self):
        """Clean up broker resources"""
        # Clean up empty topics
        self.topic_manager.cleanup_empty_topics()
        
        # Remove disconnected clients
        for client_id in list(self.session_manager.clients.keys()):
            client = self.session_manager.get_client(client_id)
            if client and not client.connected:
                self.remove_client(client_id)
    
    async def run_forever(self):
        """Run the broker indefinitely"""
        try:
            await self.start()
            
            # Keep the broker running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Broker error: {e}")
        finally:
            await self.stop() 