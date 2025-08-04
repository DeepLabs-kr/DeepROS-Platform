import asyncio
import logging
import struct
from typing import Optional, Dict, Any
from ..models.message import Message
from ..models.client import Client
from ..config import settings

logger = logging.getLogger(__name__)


class MQTTProtocol(asyncio.Protocol):
    """MQTT Protocol implementation"""
    
    # MQTT Packet Types
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14
    
    def __init__(self, broker):
        self.broker = broker
        self.transport = None
        self.client: Optional[Client] = None
        self.buffer = bytearray()
        self.keepalive_task: Optional[asyncio.Task] = None
        
    def connection_made(self, transport):
        """Called when a connection is established"""
        self.transport = transport
        logger.info(f"New connection from {transport.get_extra_info('peername')}")
    
    def connection_lost(self, exc):
        """Called when a connection is lost"""
        if self.client:
            self.broker.session_manager.disconnect_client(self.client.client_id, "Connection lost")
        if self.keepalive_task:
            self.keepalive_task.cancel()
        logger.info("Connection lost")
    
    def data_received(self, data):
        """Called when data is received"""
        self.buffer.extend(data)
        
        while len(self.buffer) >= 2:
            # Parse fixed header
            packet_type = (self.buffer[0] >> 4) & 0x0F
            remaining_length = self.buffer[1]
            
            if remaining_length == 0x7F:
                # Extended length
                if len(self.buffer) < 4:
                    return
                remaining_length = struct.unpack('!I', self.buffer[2:6])[0]
                header_length = 6
            else:
                header_length = 2
            
            packet_length = header_length + remaining_length
            
            if len(self.buffer) < packet_length:
                return
            
            # Extract packet
            packet = self.buffer[:packet_length]
            self.buffer = self.buffer[packet_length:]
            
            # Process packet
            try:
                self._handle_packet(packet_type, packet)
            except Exception as e:
                logger.error(f"Error handling packet: {e}")
    
    def _handle_packet(self, packet_type: int, packet: bytes):
        """Handle different packet types"""
        if packet_type == self.CONNECT:
            self._handle_connect(packet)
        elif packet_type == self.PUBLISH:
            self._handle_publish(packet)
        elif packet_type == self.SUBSCRIBE:
            self._handle_subscribe(packet)
        elif packet_type == self.UNSUBSCRIBE:
            self._handle_unsubscribe(packet)
        elif packet_type == self.PINGREQ:
            self._handle_pingreq(packet)
        elif packet_type == self.DISCONNECT:
            self._handle_disconnect(packet)
        else:
            logger.warning(f"Unsupported packet type: {packet_type}")
    
    def _handle_connect(self, packet: bytes):
        """Handle CONNECT packet"""
        try:
            # Parse CONNECT packet
            offset = 2  # Skip fixed header
            
            # Protocol name
            protocol_name_length = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            protocol_name = packet[offset:offset+protocol_name_length].decode('utf-8')
            offset += protocol_name_length
            
            # Protocol level
            protocol_level = packet[offset]
            offset += 1
            
            # Connect flags
            connect_flags = packet[offset]
            offset += 1
            
            clean_session = bool(connect_flags & 0x02)
            will_flag = bool(connect_flags & 0x04)
            will_qos = (connect_flags >> 3) & 0x03
            will_retain = bool(connect_flags & 0x20)
            password_flag = bool(connect_flags & 0x40)
            username_flag = bool(connect_flags & 0x80)
            
            # Keep alive
            keepalive = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            
            # Client ID
            client_id_length = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            client_id = packet[offset:offset+client_id_length].decode('utf-8')
            offset += client_id_length
            
            # Will topic and message
            will_topic = None
            will_message = None
            if will_flag:
                will_topic_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                will_topic = packet[offset:offset+will_topic_length].decode('utf-8')
                offset += will_topic_length
                
                will_message_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                will_message = packet[offset:offset+will_message_length].decode('utf-8')
                offset += will_message_length
            
            # Username and password
            username = None
            password = None
            if username_flag:
                username_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                username = packet[offset:offset+username_length].decode('utf-8')
                offset += username_length
            
            if password_flag:
                password_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                password = packet[offset:offset+password_length].decode('utf-8')
                offset += password_length
            
            # Authenticate client
            if not self.broker.session_manager.authenticate_client(client_id, username, password):
                self._send_connack(0x05)  # Not authorized
                return
            
            # Create or get client
            self.client = self.broker.session_manager.create_client(
                client_id=client_id,
                username=username,
                password=password,
                clean_session=clean_session,
                keepalive=keepalive,
                will_topic=will_topic,
                will_message=will_message,
                will_qos=will_qos,
                will_retain=will_retain
            )
            
            # Connect client
            if not self.broker.session_manager.connect_client(client_id, self.transport, self):
                self._send_connack(0x02)  # Identifier rejected
                return
            
            # Start keepalive task
            if keepalive > 0:
                self.keepalive_task = asyncio.create_task(self._keepalive_loop(keepalive))
            
            # Send CONNACK
            self._send_connack(0x00)  # Connection accepted
            
            logger.info(f"Client {client_id} connected successfully")
            
        except Exception as e:
            logger.error(f"Error handling CONNECT: {e}")
            self._send_connack(0x03)  # Server unavailable
    
    def _handle_publish(self, packet: bytes):
        """Handle PUBLISH packet"""
        if not self.client:
            return
        
        try:
            # Parse PUBLISH packet
            offset = 2  # Skip fixed header
            
            # Topic
            topic_length = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            topic = packet[offset:offset+topic_length].decode('utf-8')
            offset += topic_length
            
            # Message ID (for QoS > 0)
            message_id = None
            if self.client.qos > 0:
                message_id = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
            
            # Payload
            payload = packet[offset:]
            
            # Create message
            message = Message(
                topic=topic,
                payload=payload,
                qos=self.client.qos,
                retain=self.client.will_retain,
                client_id=self.client.client_id
            )
            
            # Publish message
            subscribers = self.broker.topic_manager.publish_message(message)
            
            # Send acknowledgments
            if self.client.qos == 1:
                self._send_puback(message_id)
            elif self.client.qos == 2:
                self._send_pubrec(message_id)
            
            logger.debug(f"Message published to {len(subscribers)} subscribers")
            
        except Exception as e:
            logger.error(f"Error handling PUBLISH: {e}")
    
    def _handle_subscribe(self, packet: bytes):
        """Handle SUBSCRIBE packet"""
        if not self.client:
            return
        
        try:
            # Parse SUBSCRIBE packet
            offset = 2  # Skip fixed header
            
            # Message ID
            message_id = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            
            # Topic filters and QoS
            topics = []
            while offset < len(packet):
                topic_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                topic = packet[offset:offset+topic_length].decode('utf-8')
                offset += topic_length
                qos = packet[offset] & 0x03
                offset += 1
                topics.append((topic, qos))
            
            # Subscribe to topics
            return_codes = []
            for topic, qos in topics:
                success = self.broker.topic_manager.subscribe(self.client.client_id, topic, qos)
                return_codes.append(qos if success else 0x80)
            
            # Send SUBACK
            self._send_suback(message_id, return_codes)
            
        except Exception as e:
            logger.error(f"Error handling SUBSCRIBE: {e}")
    
    def _handle_unsubscribe(self, packet: bytes):
        """Handle UNSUBSCRIBE packet"""
        if not self.client:
            return
        
        try:
            # Parse UNSUBSCRIBE packet
            offset = 2  # Skip fixed header
            
            # Message ID
            message_id = struct.unpack('!H', packet[offset:offset+2])[0]
            offset += 2
            
            # Topic filters
            topics = []
            while offset < len(packet):
                topic_length = struct.unpack('!H', packet[offset:offset+2])[0]
                offset += 2
                topic = packet[offset:offset+topic_length].decode('utf-8')
                offset += topic_length
                topics.append(topic)
            
            # Unsubscribe from topics
            for topic in topics:
                self.broker.topic_manager.unsubscribe(self.client.client_id, topic)
            
            # Send UNSUBACK
            self._send_unsuback(message_id)
            
        except Exception as e:
            logger.error(f"Error handling UNSUBSCRIBE: {e}")
    
    def _handle_pingreq(self, packet: bytes):
        """Handle PINGREQ packet"""
        self._send_pingresp()
        if self.client:
            self.broker.session_manager.update_client_activity(self.client.client_id)
    
    def _handle_disconnect(self, packet: bytes):
        """Handle DISCONNECT packet"""
        if self.client:
            self.broker.session_manager.disconnect_client(self.client.client_id, "Client disconnect")
        self.transport.close()
    
    def _send_connack(self, return_code: int):
        """Send CONNACK packet"""
        packet = struct.pack('!BB', 0x20, 0x02) + struct.pack('!BB', 0x00, return_code)
        self.transport.write(packet)
    
    def _send_puback(self, message_id: int):
        """Send PUBACK packet"""
        packet = struct.pack('!BBH', 0x40, 0x02, message_id)
        self.transport.write(packet)
    
    def _send_pubrec(self, message_id: int):
        """Send PUBREC packet"""
        packet = struct.pack('!BBH', 0x50, 0x02, message_id)
        self.transport.write(packet)
    
    def _send_suback(self, message_id: int, return_codes: list):
        """Send SUBACK packet"""
        payload = struct.pack('!H', message_id) + bytes(return_codes)
        packet = struct.pack('!BB', 0x90, len(payload)) + payload
        self.transport.write(packet)
    
    def _send_unsuback(self, message_id: int):
        """Send UNSUBACK packet"""
        packet = struct.pack('!BBH', 0xB0, 0x02, message_id)
        self.transport.write(packet)
    
    def _send_pingresp(self):
        """Send PINGRESP packet"""
        packet = struct.pack('!BB', 0xD0, 0x00)
        self.transport.write(packet)
    
    def send_message(self, message: Message, qos: int = 0):
        """Send a message to the client"""
        if not self.transport:
            return
        
        try:
            # Build PUBLISH packet
            topic_bytes = message.topic.encode('utf-8')
            topic_length = len(topic_bytes)
            
            # Fixed header
            packet_type = 0x30  # PUBLISH
            remaining_length = 2 + topic_length + len(message.payload)
            if qos > 0:
                remaining_length += 2  # Message ID
            
            if remaining_length < 128:
                fixed_header = struct.pack('!BB', packet_type, remaining_length)
            else:
                # Extended length
                fixed_header = struct.pack('!BI', packet_type, remaining_length)
            
            # Variable header
            variable_header = struct.pack('!H', topic_length) + topic_bytes
            if qos > 0:
                message_id = self.broker.session_manager.get_next_message_id()
                variable_header += struct.pack('!H', message_id)
            
            # Payload
            payload = message.payload
            
            # Send packet
            packet = fixed_header + variable_header + payload
            self.transport.write(packet)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def _keepalive_loop(self, keepalive: int):
        """Keepalive loop"""
        while True:
            try:
                await asyncio.sleep(keepalive)
                if self.client and self.client.connected:
                    # Check if client is still active
                    if self.client.is_idle(keepalive * 2):
                        logger.info(f"Client {self.client.client_id} timed out")
                        self.broker.session_manager.disconnect_client(self.client.client_id, "Keepalive timeout")
                        break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in keepalive loop: {e}")
                break 