from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

from app.models.user import UserRole

class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$')
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    role: UserRole

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Schema for user registration with password validation."""
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., min_length=8, example="SecurePass123!")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$')
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

    @validator("nickname", pre=True, always=True)
    def generate_nickname(cls, v, values):
        """Generate a nickname from email if not provided."""
        if not v and "email" in values:
            # Take the part before @ and remove special characters
            email_name = values["email"].split("@")[0]
            import re
            nickname = re.sub(r'[^a-zA-Z0-9_-]', '', email_name)
            return nickname
        return v

class UserResponse(UserBase):
    """Schema for user response after registration."""
    id: UUID
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
