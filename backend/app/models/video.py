# backend/app/models/video.py
"""
Video model for database ORM.
Defines the structure of the videos table and relationships.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class VideoStatus(str, enum.Enum):
    """Enum for video processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Video(Base):
    """
    Video model representing a video in the system.
    
    Attributes:
        id: Unique identifier for the video
        title: Video title
        description: Video description
        filename: Original filename
        file_size: Size of the original video in bytes
        duration: Video duration in seconds
        status: Current processing status
        thumbnail_url: URL to the video thumbnail
        original_url: URL to the original uploaded video
        processed_urls: JSON array of processed video URLs (different resolutions)
        metadata: JSON object for additional video metadata
        user_id: Foreign key to the user who owns this video
        created_at: Timestamp when video was uploaded
        updated_at: Timestamp when video was last updated
        owner: Relationship to the user who owns this video
    """
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)  # Size in bytes
    duration = Column(Integer)  # Duration in seconds
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    thumbnail_url = Column(String)
    original_url = Column(String)
    processed_urls = Column(JSON, default=dict)  # Store URLs for different resolutions
    metadata = Column(JSON, default=dict)  # Additional metadata
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship: Many videos belong to one user
    owner = relationship("User", back_populates="videos")
    
    def __repr__(self) -> str:
        """String representation of the video"""
        return f"<Video {self.title}>"