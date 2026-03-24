# backend/app/workers/tasks.py
"""
Celery task definitions for async video processing.
"""

import os
import tempfile
import logging
from typing import Dict, Any
from celery import Task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.services.video_processor import video_processor
from app.services.s3_service import s3_service
from app.core.database import SessionLocal
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoProcessingStatus
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

class VideoProcessingTask(Task):
    """
    Custom task class for video processing with database cleanup.
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called if task fails.
        Updates video status to FAILED in database.
        """
        video_id = kwargs.get("video_id")
        if video_id:
            db = SessionLocal()
            try:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.FAILED
                    video.metadata = {
                        **video.metadata,
                        "error": str(exc),
                        "error_time": str(datetime.utcnow())
                    }
                    db.commit()
                    
                    # Send WebSocket notification
                    asyncio.create_task(
                        manager.send_personal_message(
                            json.dumps(VideoProcessingStatus(
                                video_id=video_id,
                                status=VideoStatus.FAILED,
                                error=str(exc)
                            ).dict()),
                            user_id=video.user_id
                        )
                    )
            finally:
                db.close()

@celery_app.task(
    bind=True,
    base=VideoProcessingTask,
    name="app.workers.tasks.process_video",
    queue="video_processing"
)
def process_video(self, video_id: int, user_id: int, file_url: str):
    """
    Main video processing task.
    Downloads video, processes it, and uploads results.
    
    Args:
        video_id: Database ID of the video
        user_id: ID of the user who owns the video
        file_url: URL of the uploaded video file
    """
    db = SessionLocal()
    temp_file = None
    
    try:
        # Update video status to PROCESSING
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception(f"Video {video_id} not found")
        
        video.status = VideoStatus.PROCESSING
        db.commit()
        
        # Send WebSocket update
        asyncio.create_task(
            manager.send_personal_message(
                json.dumps(VideoProcessingStatus(
                    video_id=video_id,
                    status=VideoStatus.PROCESSING,
                    progress=0,
                    message="Starting video processing..."
                ).dict()),
                user_id=user_id
            )
        )
        
        # Download video to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(video.filename)[1],
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Download file from S3 (or directly from URL)
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            with open(temp_path, "wb") as f:
                f.write(response.content)
        
        # Update progress
        asyncio.create_task(
            manager.send_personal_message(
                json.dumps(VideoProcessingStatus(
                    video_id=video_id,
                    status=VideoStatus.PROCESSING,
                    progress=20,
                    message="Downloaded video, starting processing..."
                ).dict()),
                user_id=user_id
            )
        )
        
        # Process video
        results = await video_processor.process_video(
            temp_path,
            video_id,
            user_id
        )
        
        # Update progress
        asyncio.create_task(
            manager.send_personal_message(
                json.dumps(VideoProcessingStatus(
                    video_id=video_id,
                    status=VideoStatus.PROCESSING,
                    progress=80,
                    message="Processing complete, uploading results..."
                ).dict()),
                user_id=user_id
            )
        )
        
        # Update video metadata in database
        video.duration = results["metadata"].get("duration")
        video.file_size = results["metadata"].get("file_size")
        video.thumbnail_url = results["thumbnails"][0] if results["thumbnails"] else None
        video.processed_urls = results["processed_videos"]
        video.metadata = results["metadata"]
        video.status = VideoStatus.COMPLETED
        db.commit()
        
        # Send completion notification
        asyncio.create_task(
            manager.send_personal_message(
                json.dumps(VideoProcessingStatus(
                    video_id=video_id,
                    status=VideoStatus.COMPLETED,
                    progress=100,
                    message="Video processing completed successfully!"
                ).dict()),
                user_id=user_id
            )
        )
        
        logger.info(f"Successfully processed video {video_id}")
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        video.status = VideoStatus.FAILED
        video.metadata = {
            **video.metadata,
            "error": str(e),
            "error_time": str(datetime.utcnow())
        }
        db.commit()
        raise
        
    finally:
        # Clean up temporary files
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)
        db.close()

@celery_app.task(
    name="app.workers.tasks.cleanup_temp_files",
    queue="cleanup"
)
def cleanup_temp_files():
    """
    Periodic task to clean up old temporary files.
    """
    temp_dir = tempfile.gettempdir()
    import time
    from datetime import datetime, timedelta
    
    # Remove files older than 24 hours
    cutoff_time = time.time() - (24 * 3600)
    
    for filename in os.listdir(temp_dir):
        if filename.startswith("tmp") or filename.startswith("vidflow"):
            filepath = os.path.join(temp_dir, filename)
            try:
                if os.path.getmtime(filepath) < cutoff_time:
                    os.unlink(filepath)
                    logger.info(f"Cleaned up old temp file: {filepath}")
            except Exception as e:
                logger.error(f"Error cleaning up {filepath}: {str(e)}")
    
    return {"status": "success", "message": "Cleanup completed"}

@celery_app.task(
    name="app.workers.tasks.update_video_analytics",
    queue="cleanup"
)
def update_video_analytics():
    """
    Periodic task to update video analytics (views, etc.).
    """
    # This is a placeholder for analytics updates
    # You could implement video view counting, popularity scores, etc.
    logger.info("Updating video analytics...")
    return {"status": "success", "message": "Analytics updated"}