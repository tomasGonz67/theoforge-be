# Pydantic models for request/response validation
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    role: UserRole = Field(default=UserRole.USER)

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str = Field(..., example="strongpassword123")

class UserResponse(UserBase):
    id: UUID
    email_verified: bool
    is_locked: bool
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="strongpassword123")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# TODO: Define UserUpdate
# TODO: Define UserInDB

"""
Fields not included:
nickname
first/last name
bio
profile URLs
professional status

Validators not included:
URL validation
Update validation
Pagination schemas

Added only essential fields for auth
Simplified response models
"""