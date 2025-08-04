import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from ..models.client import Client
from ..config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages MQTT client sessions and connections"""
    
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.next_message_id = 1
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the session manager"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")
    
    async def stop(self):
        """Stop the session manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Session manager stopped")
    
    def create_client(self, client_id: str, **kwargs) -> Client:
        """Create a new client session"""
        if client_id in self.clients:
            logger.warning(f"Client {client_id} already exists, reusing existing session")
            return self.clients[client_id]
        
        client = Client(client_id=client_id, **kwargs)
        self.clients[client_id] = client
        logger.info(f"Created new client session: {client_id}")
        return client
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get a client by ID"""
        return self.clients.get(client_id)
    
    def authenticate_client(self, client_id: str, username: str = None, password: str = None) -> bool:
        """Authenticate a client"""
        if not settings.enable_auth:
            return True
        
        if not username or not password:
            logger.warning(f"Authentication failed for client {client_id}: missing credentials")
            return False
        
        if username != settings.username or password != settings.password:
            logger.warning(f"Authentication failed for client {client_id}: invalid credentials")
            return False
        
        logger.info(f"Client {client_id} authenticated successfully")
        return True
    
    def connect_client(self, client_id: str, transport: asyncio.Transport, protocol: asyncio.Protocol) -> bool:
        """Connect a client"""
        client = self.get_client(client_id)
        if not client:
            logger.error(f"Cannot connect unknown client: {client_id}")
            return False
        
        # Check if client is already connected
        if client.connected:
            logger.warning(f"Client {client_id} is already connected")
            return False
        
        client.connect(transport, protocol)
        logger.info(f"Client {client_id} connected")
        return True
    
    def disconnect_client(self, client_id: str, reason: str = "Unknown"):
        """Disconnect a client"""
        client = self.get_client(client_id)
        if not client:
            logger.warning(f"Cannot disconnect unknown client: {client_id}")
            return
        
        client.disconnect()
        logger.info(f"Client {client_id} disconnected: {reason}")
    
    def remove_client(self, client_id: str):
        """Remove a client session"""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Removed client session: {client_id}")
    
    def update_client_activity(self, client_id: str):
        """Update client's last activity timestamp"""
        client = self.get_client(client_id)
        if client:
            client.update_last_seen()
    
    def get_connected_clients(self) -> List[Client]:
        """Get all connected clients"""
        return [client for client in self.clients.values() if client.connected]
    
    def get_client_count(self) -> int:
        """Get total number of clients"""
        return len(self.clients)
    
    def get_connected_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.get_connected_clients())
    
    def get_next_message_id(self) -> int:
        """Get next available message ID"""
        message_id = self.next_message_id
        self.next_message_id = (self.next_message_id % 65535) + 1
        return message_id
    
    def is_client_connected(self, client_id: str) -> bool:
        """Check if a client is connected"""
        client = self.get_client(client_id)
        return client is not None and client.connected
    
    def get_client_info(self, client_id: str) -> Optional[dict]:
        """Get client information"""
        client = self.get_client(client_id)
        if not client:
            return None
        
        return {
            'client_id': client.client_id,
            'username': client.username,
            'connected': client.connected,
            'connected_at': client.connected_at.isoformat() if client.connected_at else None,
            'last_seen': client.last_seen.isoformat() if client.last_seen else None,
            'subscriptions': list(client.subscriptions),
            'inflight_messages': len(client.inflight_messages),
            'queued_messages': len(client.queued_messages),
        }
    
    def get_all_clients_info(self) -> List[dict]:
        """Get information about all clients"""
        return [self.get_client_info(client_id) for client_id in self.clients.keys()]
    
    def get_idle_clients(self, timeout_seconds: int = 300) -> List[str]:
        """Get list of idle client IDs"""
        idle_clients = []
        for client_id, client in self.clients.items():
            if client.is_idle(timeout_seconds):
                idle_clients.append(client_id)
        return idle_clients
    
    async def _cleanup_loop(self):
        """Background task to clean up idle clients"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_idle_clients()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_idle_clients(self):
        """Clean up idle clients"""
        idle_timeout = 300  # 5 minutes
        idle_clients = self.get_idle_clients(idle_timeout)
        
        for client_id in idle_clients:
            client = self.get_client(client_id)
            if client and client.connected:
                logger.info(f"Disconnecting idle client: {client_id}")
                client.disconnect()
    
    def get_statistics(self) -> dict:
        """Get session manager statistics"""
        connected_clients = self.get_connected_clients()
        total_subscriptions = sum(len(client.subscriptions) for client in self.clients.values())
        total_inflight = sum(len(client.inflight_messages) for client in self.clients.values())
        total_queued = sum(len(client.queued_messages) for client in self.clients.values())
        
        return {
            'total_clients': len(self.clients),
            'connected_clients': len(connected_clients),
            'total_subscriptions': total_subscriptions,
            'total_inflight_messages': total_inflight,
            'total_queued_messages': total_queued,
            'next_message_id': self.next_message_id,
        } 