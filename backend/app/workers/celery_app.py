# backend/app/workers/celery_app.py
"""
Celery application configuration for distributed task processing.
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "vidflow",
    broker=settings.RABBITMQ_URL,  # Use RabbitMQ as message broker
    backend=settings.REDIS_URL,    # Use Redis for result backend
    include=["app.workers.tasks"]  # Import tasks module
)

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only prefetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    
    # Task routing
    task_routes={
        "app.workers.tasks.process_video": {"queue": "video_processing"},
        "app.workers.tasks.generate_thumbnail": {"queue": "thumbnail_generation"},
        "app.workers.tasks.cleanup_temp_files": {"queue": "cleanup"},
    },
    
    # Periodic tasks (Celery Beat)
    beat_schedule={
        "cleanup-temp-files": {
            "task": "app.workers.tasks.cleanup_temp_files",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "update-video-analytics": {
            "task": "app.workers.tasks.update_video_analytics",
            "schedule": crontab(minute="0", hour="*/1"),  # Every hour
        },
    }
)

# Optional: Configure task queues
celery_app.conf.task_queues = {
    "video_processing": {
        "exchange": "video_processing",
        "routing_key": "video_processing",
    },
    "thumbnail_generation": {
        "exchange": "thumbnail_generation",
        "routing_key": "thumbnail_generation",
    },
    "cleanup": {
        "exchange": "cleanup",
        "routing_key": "cleanup",
    },
}