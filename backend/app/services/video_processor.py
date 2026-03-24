# backend/app/services/video_processor.py
"""
Video processing service using moviepy.
Handles video transcoding, thumbnail generation, and metadata extraction.
"""

import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from PIL import Image
import moviepy.editor as mp
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Service for processing videos.
    Handles transcoding, thumbnail generation, and metadata extraction.
    """
    
    def __init__(self):
        """Initialize video processor with thread pool for async operations"""
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def extract_metadata(self, video_path: str) -> Dict:
        """
        Extract metadata from video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict: Video metadata including duration, dimensions, etc.
        """
        try:
            # Run metadata extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                self.executor,
                self._extract_metadata_sync,
                video_path
            )
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise
    
    def _extract_metadata_sync(self, video_path: str) -> Dict:
        """
        Synchronous metadata extraction.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict: Video metadata
        """
        try:
            video = mp.VideoFileClip(video_path)
            
            metadata = {
                "duration": video.duration,
                "fps": video.fps,
                "size": video.size,
                "rotation": video.rotation,
                "filename": os.path.basename(video_path),
                "file_size": os.path.getsize(video_path)
            }
            
            video.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error in synchronous metadata extraction: {str(e)}")
            raise
    
    async def generate_thumbnail(
        self,
        video_path: str,
        time_position: float = 1.0,
        size: Tuple[int, int] = (320, 180)
    ) -> str:
        """
        Generate a thumbnail from video.
        
        Args:
            video_path: Path to the video file
            time_position: Time position to capture thumbnail (seconds)
            size: Thumbnail dimensions (width, height)
            
        Returns:
            str: Path to generated thumbnail file
        """
        try:
            loop = asyncio.get_event_loop()
            thumbnail_path = await loop.run_in_executor(
                self.executor,
                self._generate_thumbnail_sync,
                video_path,
                time_position,
                size
            )
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            raise
    
    def _generate_thumbnail_sync(
        self,
        video_path: str,
        time_position: float,
        size: Tuple[int, int]
    ) -> str:
        """
        Synchronous thumbnail generation.
        
        Args:
            video_path: Path to the video file
            time_position: Time position to capture thumbnail
            size: Thumbnail dimensions
            
        Returns:
            str: Path to generated thumbnail file
        """
        try:
            video = mp.VideoFileClip(video_path)
            
            # Extract frame at specified time
            frame = video.get_frame(time_position)
            
            # Convert to PIL Image
            img = Image.fromarray(frame)
            
            # Resize image
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_dir = Path(tempfile.gettempdir()) / "thumbnails"
            thumbnail_dir.mkdir(exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"thumbnail_{os.path.basename(video_path)}.jpg"
            img.save(thumbnail_path, "JPEG", quality=85)
            
            video.close()
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Error in synchronous thumbnail generation: {str(e)}")
            raise
    
    async def transcode_video(
        self,
        video_path: str,
        output_path: str,
        resolution: str
    ) -> str:
        """
        Transcode video to specified resolution.
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            resolution: Target resolution (e.g., "720p")
            
        Returns:
            str: Path to transcoded video
        """
        try:
            # Define FFmpeg parameters based on resolution
            resolution_map = {
                "1080p": {"width": 1920, "height": 1080, "bitrate": "5000k"},
                "720p": {"width": 1280, "height": 720, "bitrate": "2500k"},
                "480p": {"width": 854, "height": 480, "bitrate": "1000k"},
                "360p": {"width": 640, "height": 360, "bitrate": "500k"}
            }
            
            if resolution not in resolution_map:
                raise ValueError(f"Unsupported resolution: {resolution}")
            
            params = resolution_map[resolution]
            
            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"scale={params['width']}:{params['height']}:force_original_aspect_ratio=decrease,pad={params['width']}:{params['height']}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-b:v", params["bitrate"],
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                output_path
            ]
            
            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error transcoding video: {str(e)}")
            raise
    
    async def process_video(
        self,
        input_path: str,
        video_id: int,
        user_id: int
    ) -> Dict:
        """
        Complete video processing pipeline.
        
        Args:
            input_path: Path to input video
            video_id: Video ID in database
            user_id: User ID who owns the video
            
        Returns:
            Dict: Processing results with metadata and URLs
        """
        results = {
            "metadata": {},
            "thumbnails": [],
            "processed_videos": {},
            "success": False
        }
        
        try:
            # Extract metadata
            logger.info(f"Extracting metadata for video {video_id}")
            metadata = await self.extract_metadata(input_path)
            results["metadata"] = metadata
            
            # Generate thumbnail
            logger.info(f"Generating thumbnail for video {video_id}")
            thumbnail_path = await self.generate_thumbnail(input_path)
            
            # Upload thumbnail to S3
            with open(thumbnail_path, "rb") as f:
                thumbnail_key = f"thumbnails/video_{video_id}.jpg"
                # TODO: Upload to S3 and get URL
                results["thumbnails"].append("thumbnail_url")
            
            # Process different resolutions
            for resolution in settings.PROCESSING_RESOLUTIONS:
                logger.info(f"Transcoding video {video_id} to {resolution}")
                
                # Create temporary output file
                output_file = tempfile.NamedTemporaryFile(
                    suffix=".mp4",
                    delete=False
                )
                output_path = output_file.name
                output_file.close()
                
                # Transcode video
                await self.transcode_video(
                    input_path,
                    output_path,
                    resolution
                )
                
                # Upload processed video to S3
                with open(output_path, "rb") as f:
                    video_key = f"processed/{video_id}/{resolution}.mp4"
                    # TODO: Upload to S3 and get URL
                    results["processed_videos"][resolution] = "video_url"
                
                # Clean up temporary file
                os.unlink(output_path)
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {str(e)}")
            results["error"] = str(e)
            raise
        
        finally:
            # Clean up input file
            if os.path.exists(input_path):
                os.unlink(input_path)
        
        return results

# Create global video processor instance
video_processor = VideoProcessor()