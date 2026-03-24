# backend/app/api/v1/router.py
"""
Main API router for version 1.
Includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import upload, videos, websocket, auth

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])