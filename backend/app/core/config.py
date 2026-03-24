# backend/app/core/config.py
"""
Application configuration management using Pydantic Settings.
Handles environment variables and provides typed configuration.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by setting environment variables
    with the same name (case-insensitive).
    """
    
    # Application Settings
    APP_NAME: str = Field(default="VidFlow", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # Required field
    
    # Database Settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_TEST_URL: Optional[str] = Field(default=None, env="DATABASE_TEST_URL")
    
    # Redis Settings
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_BROKER_URL: str = Field(..., env="REDIS_BROKER_URL")
    
    # RabbitMQ Settings
    RABBITMQ_URL: str = Field(..., env="RABBITMQ_URL")
    
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    S3_BUCKET_NAME: str = Field(..., env="S3_BUCKET_NAME")
    S3_BUCKET_PROCESSED: str = Field(..., env="S3_BUCKET_PROCESSED")
    
    # CloudFront Settings
    CLOUDFRONT_DOMAIN: Optional[str] = Field(default=None, env="CLOUDFRONT_DOMAIN")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Video Processing Settings
    MAX_VIDEO_SIZE: int = Field(default=1073741824, env="MAX_VIDEO_SIZE")  # 1GB
    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(
        default=[".mp4", ".mov", ".avi", ".mkv", ".webm"],
        env="ALLOWED_VIDEO_EXTENSIONS"
    )
    PROCESSING_RESOLUTIONS: List[str] = Field(
        default=["1080p", "720p", "480p", "360p"],
        env="PROCESSING_RESOLUTIONS"
    )
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from string to list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("PROCESSING_RESOLUTIONS", pre=True)
    def parse_resolutions(cls, v):
        """Parse processing resolutions from string to list"""
        if isinstance(v, str):
            return [res.strip() for res in v.split(",")]
        return v
    
    @property
    def CLOUDFRONT_URL(self) -> Optional[str]:
        """Get CloudFront base URL"""
        if self.CLOUDFRONT_DOMAIN:
            return f"https://{self.CLOUDFRONT_DOMAIN}"
        return None
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings instance
settings = Settings()