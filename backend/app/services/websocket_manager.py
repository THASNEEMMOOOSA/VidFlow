# backend/app/services/websocket_manager.py
"""
WebSocket connection manager for handling real-time connections.
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    """
    
    def __init__(self):
        """Initialize connection manager with active connections."""
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_subscriptions: Dict[int, Set[int]] = {}  # user_id -> set of video_ids
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept a new WebSocket connection and store it.
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the connected user
        """
        await websocket.accept()
        
        async with self._lock:
            self.active_connections[user_id] = websocket
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        """
        Remove a disconnected WebSocket connection.
        
        Args:
            user_id: ID of the disconnected user
        """
        async with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]
        
        logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, user_id: int):
        """
        Send a message to a specific user.
        
        Args:
            message: The message to send
            user_id: ID of the recipient user
        """
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
                logger.debug(f"Sent personal message to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                self.disconnect(user_id)
    
    async def broadcast_to_video_subscribers(self, message: str, video_id: int):
        """
        Send a message to all users subscribed to a specific video.
        
        Args:
            message: The message to send
            video_id: ID of the video
        """
        sent_count = 0
        
        async with self._lock:
            for user_id, subscriptions in self.user_subscriptions.items():
                if video_id in subscriptions and user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_text(message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
        
        logger.debug(f"Broadcasted to {sent_count} subscribers for video {video_id}")
    
    async def broadcast_to_all(self, message: str):
        """
        Broadcast a message to all connected users.
        
        Args:
            message: The message to broadcast
        """
        async with self._lock:
            connections = list(self.active_connections.items())
        
        for user_id, websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                self.disconnect(user_id)
    
    async def send_processing_update(
        self,
        video_id: int,
        user_id: int,
        status: str,
        progress: Optional[int] = None,
        message: Optional[str] = None
    ):
        """
        Send a video processing status update.
        
        Args:
            video_id: ID of the video being processed
            user_id: ID of the user who owns the video
            status: Current processing status
            progress: Optional progress percentage
            message: Optional status message
        """
        update = {
            "type": "video_status",
            "video_id": video_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": str(datetime.utcnow())
        }
        
        # Send to the video owner
        await self.send_personal_message(json.dumps(update), user_id)
        
        # Also broadcast to any subscribers
        await self.broadcast_to_video_subscribers(json.dumps(update), video_id)
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "info"
    ):
        """
        Send a notification to a specific user.
        
        Args:
            user_id: ID of the recipient user
            title: Notification title
            body: Notification body
            notification_type: Type of notification (info, success, warning, error)
        """
        notification = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "timestamp": str(datetime.utcnow())
        }
        
        await self.send_personal_message(json.dumps(notification), user_id)
    
    def is_connected(self, user_id: int) -> bool:
        """
        Check if a user is currently connected.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user is connected, False otherwise
        """
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            int: Number of active WebSocket connections
        """
        return len(self.active_connections)

# Create global connection manager instance
manager = ConnectionManager()