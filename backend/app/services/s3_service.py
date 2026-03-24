# backend/app/services/s3_service.py
"""
S3 service for handling file operations with AWS S3.
"""

import boto3
import os
import uuid
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    """
    Service for interacting with AWS S3.
    Handles file uploads, downloads, and management.
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from settings"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.processed_bucket = settings.S3_BUCKET_PROCESSED
        
    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "uploads",
        custom_key: Optional[str] = None
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            file: The uploaded file object
            folder: Folder path within the bucket
            custom_key: Optional custom key for the file
            
        Returns:
            str: The S3 URL of the uploaded file
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Generate a unique filename if not provided
            if not custom_key:
                file_extension = os.path.splitext(file.filename)[1]
                unique_id = uuid.uuid4().hex
                filename = f"{unique_id}{file_extension}"
                key = f"{folder}/{filename}"
            else:
                key = custom_key
            
            # Read file content
            content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=file.content_type
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            logger.info(f"File uploaded successfully: {key}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            key: The S3 key of the file to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"File deleted successfully: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    async def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate a presigned URL for temporary access to a private file.
        
        Args:
            key: The S3 key of the file
            expiration: URL expiration time in seconds
            
        Returns:
            str: Presigned URL for the file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
    
    async def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            key: The S3 key of the file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError:
            return False

# Create a global instance of S3 service
s3_service = S3Service()