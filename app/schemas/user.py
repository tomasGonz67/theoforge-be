from builtins import ValueError, str
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid
import re
from app.models.user_model import UserRole
from app.utils.nickname_gen import generate_nickname

class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example=generate_nickname())
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    role: UserRole

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Schema for user registration with password validation."""
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., min_length=8, example="SecurePass123!")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")

    @validator("password")
    def validate_password(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserResponse(UserBase):
    """Schema for user response after registration."""
    id: uuid.UUID = Field(..., example=uuid.uuid4())
    email_verified: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(None, example="The requested resource was not found.")

"""
Changes made to align with User model:
1. Removed non-registration fields:
   - Profile fields (bio, URLs)
   - Professional status
   - Login-related fields
2. Added password validation in UserCreate
3. Removed CRUD-related schemas (UserUpdate, UserListResponse)
4. Removed auth-related schemas (LoginRequest)
"""
