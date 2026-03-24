# backend/app/schemas/user.py
"""
Pydantic schemas for user data validation and serialization.
These define the structure of request and response data for user endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# Base User Schema - Contains common fields
class UserBase(BaseModel):
    """Base user schema with common attributes"""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    
    class Config:
        from_attributes = True  # Enables ORM mode for Pydantic v2

# Create User Request Schema
class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User's password")

# Update User Request Schema
class UserUpdate(BaseModel):
    """Schema for updating an existing user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

# User Response Schema
class UserResponse(UserBase):
    """Schema for user response data"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# Login Request Schema
class UserLogin(BaseModel):
    """Schema for user login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User's password")

# Token Response Schema
class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"

# Token Payload Schema
class TokenPayload(BaseModel):
    """Schema for token payload data"""
    sub: Optional[str] = None
    exp: Optional[datetime] = None