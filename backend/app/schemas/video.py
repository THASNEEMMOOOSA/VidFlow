# backend/app/schemas/video.py
"""
Pydantic schemas for video data validation and serialization.
These define the structure of request and response data for video endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class VideoStatusEnum(str, Enum):
    """Enum for video status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Base Video Schema
class VideoBase(BaseModel):
    """Base video schema with common attributes"""
    title: str = Field(..., min_length=1, max_length=200, description="Video title")
    description: Optional[str] = Field(None, max_length=2000, description="Video description")
    
    class Config:
        from_attributes = True

# Create Video Request Schema
class VideoCreate(VideoBase):
    """Schema for creating a new video record"""
    filename: str
    file_size: int
    duration: Optional[int] = None

# Update Video Request Schema
class VideoUpdate(BaseModel):
    """Schema for updating an existing video"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[VideoStatusEnum] = None

# Video Response Schema
class VideoResponse(VideoBase):
    """Schema for video response data"""
    id: int
    filename: str
    file_size: int
    duration: Optional[int] = None
    status: VideoStatusEnum
    thumbnail_url: Optional[str] = None
    original_url: Optional[str] = None
    processed_urls: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Video Upload Response Schema
class VideoUploadResponse(BaseModel):
    """Schema for video upload response"""
    video_id: int
    status: VideoStatusEnum
    message: str
    upload_url: Optional[str] = None

# Video Processing Status Schema
class VideoProcessingStatus(BaseModel):
    """Schema for video processing status updates"""
    video_id: int
    status: VideoStatusEnum
    progress: Optional[int] = Field(None, ge=0, le=100, description="Processing progress percentage")
    message: Optional[str] = None
    error: Optional[str] = None

# Video Stream URL Schema
class VideoStreamURL(BaseModel):
    """Schema for video streaming URLs"""
    video_id: int
    title: str
    thumbnail_url: Optional[str] = None
    stream_urls: Dict[str, str]  # Resolution to URL mapping
    hls_url: Optional[str] = None  # HLS manifest URL
    dash_url: Optional[str] = None  # DASH manifest URL