# backend/app/api/v1/endpoints/videos.py
"""
Video management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    VideoResponse,
    VideoUpdate,
    VideoStreamURL
)
from app.services.streaming import streaming_service
from app.services.s3_service import s3_service

router = APIRouter()

@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[VideoStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all videos for the current user.
    
    - **skip**: Number of videos to skip (pagination)
    - **limit**: Maximum number of videos to return
    - **status**: Filter by video status
    - **search**: Search in title and description
    """
    query = db.query(Video).filter(Video.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Video.status == status)
    
    if search:
        query = query.filter(
            (Video.title.ilike(f"%{search}%")) |
            (Video.description.ilike(f"%{search}%"))
        )
    
    # Order by newest first
    query = query.order_by(desc(Video.created_at))
    
    # Apply pagination
    videos = query.offset(skip).limit(limit).all()
    
    return videos

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific video.
    """
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    return video

@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update video metadata.
    """
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Update fields
    update_data = video_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)
    
    db.commit()
    db.refresh(video)
    
    return video

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a video and all associated files.
    """
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Delete files from S3
    try:
        # Delete original video
        if video.original_url:
            # Extract key from URL
            key = video.original_url.split(f"{s3_service.bucket_name}/")[1]
            await s3_service.delete_file(key)
        
        # Delete thumbnail
        if video.thumbnail_url:
            key = video.thumbnail_url.split(f"{s3_service.bucket_name}/")[1]
            await s3_service.delete_file(key)
        
        # Delete processed videos
        for resolution, url in video.processed_urls.items():
            if url:
                key = url.split(f"{s3_service.processed_bucket}/")[1]
                await s3_service.delete_file(key)
                
    except Exception as e:
        # Log error but continue with deletion from database
        print(f"Error deleting S3 files: {str(e)}")
    
    # Delete from database
    db.delete(video)
    db.commit()

@router.get("/{video_id}/stream", response_model=VideoStreamURL)
async def get_stream_urls(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get streaming URLs for a video.
    """
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is still processing"
        )
    
    # Generate streaming URLs
    stream_urls = await streaming_service.get_streaming_urls(video)
    
    return VideoStreamURL(
        video_id=video.id,
        title=video.title,
        thumbnail_url=video.thumbnail_url,
        stream_urls=stream_urls["stream_urls"],
        hls_url=stream_urls.get("hls_url"),
        dash_url=stream_urls.get("dash_url")
    )