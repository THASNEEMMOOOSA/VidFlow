# backend/app/api/v1/endpoints/upload.py
"""
Video upload endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoUploadResponse
from app.services.s3_service import s3_service
from app.workers.tasks import process_video
from app.core.config import settings

router = APIRouter()

@router.post("/video", response_model=VideoUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a video file for processing.
    
    - **file**: Video file to upload (max 1GB)
    - **title**: Optional video title (defaults to filename)
    - **description**: Optional video description
    """
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end of file
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning
    
    if file_size > settings.MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE / (1024*1024):.0f}MB"
        )
    
    try:
        # Create video record in database
        video = Video(
            title=title or file.filename,
            description=description or "",
            filename=file.filename,
            file_size=file_size,
            status=VideoStatus.PENDING,
            user_id=current_user.id
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Upload file to S3
        s3_key = f"uploads/{current_user.id}/{video.id}_{file.filename}"
        file_url = await s3_service.upload_file(file, custom_key=s3_key)
        
        # Update video record with S3 URL
        video.original_url = file_url
        db.commit()
        
        # Trigger async video processing
        process_video.delay(
            video_id=video.id,
            user_id=current_user.id,
            file_url=file_url
        )
        
        return VideoUploadResponse(
            video_id=video.id,
            status=video.status,
            message="Video uploaded successfully. Processing started.",
            upload_url=file_url
        )
        
    except Exception as e:
        # Rollback database transaction
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/thumbnail/{video_id}")
async def upload_thumbnail(
    video_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a custom thumbnail for a video.
    """
    # Verify video belongs to user
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Validate image file
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are allowed"
        )
    
    # Upload thumbnail
    s3_key = f"thumbnails/{current_user.id}/{video_id}.jpg"
    thumbnail_url = await s3_service.upload_file(file, custom_key=s3_key)
    
    # Update video record
    video.thumbnail_url = thumbnail_url
    db.commit()
    
    return {
        "message": "Thumbnail uploaded successfully",
        "thumbnail_url": thumbnail_url
    }