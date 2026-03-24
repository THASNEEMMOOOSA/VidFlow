# backend/app/api/v1/endpoints/websocket.py
"""
WebSocket endpoints for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from typing import Dict
import json
import logging

from app.core.dependencies import get_current_user_ws
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    user = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for receiving real-time notifications.
    
    This endpoint is used to receive video processing status updates,
    notifications, and other real-time events.
    """
    await manager.connect(websocket, user.id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": "Connected to VidFlow notifications",
                "user_id": user.id
            }),
            user.id
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Handle incoming messages
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond to ping with pong
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    user.id
                )
            
            elif message_type == "subscribe":
                # Subscribe to specific video updates
                video_id = message.get("video_id")
                if video_id:
                    # Add to user's subscriptions
                    if user.id not in manager.user_subscriptions:
                        manager.user_subscriptions[user.id] = set()
                    manager.user_subscriptions[user.id].add(video_id)
                    
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "video_id": video_id,
                            "message": f"Subscribed to updates for video {video_id}"
                        }),
                        user.id
                    )
            
            elif message_type == "unsubscribe":
                # Unsubscribe from video updates
                video_id = message.get("video_id")
                if video_id and user.id in manager.user_subscriptions:
                    manager.user_subscriptions[user.id].discard(video_id)
                    
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "unsubscribed",
                            "video_id": video_id,
                            "message": f"Unsubscribed from updates for video {video_id}"
                        }),
                        user.id
                    )
            
    except WebSocketDisconnect:
        manager.disconnect(user.id)
        logger.info(f"User {user.id} disconnected from WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {str(e)}")
        manager.disconnect(user.id)