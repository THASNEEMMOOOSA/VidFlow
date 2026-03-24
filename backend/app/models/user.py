# backend/app/models/user.py
"""
User model for database ORM.
Defines the structure of the users table and relationships.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    """
    User model representing a user in the system.
    
    Attributes:
        id: Unique identifier for the user
        email: User's email address (unique)
        username: User's chosen username (unique)
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        is_superuser: Whether the user has admin privileges
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        videos: Relationship to videos owned by this user
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship: One user can have many videos
    # This creates a one-to-many relationship with the Video model
    videos = relationship("Video", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """String representation of the user"""
        return f"<User {self.username}>"