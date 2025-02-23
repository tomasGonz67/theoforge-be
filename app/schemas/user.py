from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from uuid import UUID

from app.models.user import UserRole

class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr = Field(..., description="User's email address")
    nickname: Optional[str] = Field(None, description="User's nickname")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    """Schema for user registration with password validation."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    nickname: Optional[str] = Field(None, description="User's nickname")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "nickname": "johndoe",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
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

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Validate nickname format."""
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError("ensure this value has at least 3 characters")
        if len(v) > 50:
            raise ValueError("ensure this value has at most 50 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("string does not match regex")
        return v

    @model_validator(mode='before')
    @classmethod
    def generate_nickname(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a nickname from email if not provided."""
        if isinstance(data, dict) and not data.get('nickname') and 'email' in data:
            # Take the part before @ and remove special characters
            email_name = data['email'].split('@')[0]
            import re
            data['nickname'] = re.sub(r'[^a-zA-Z0-9_-]', '', email_name)
        return data

class UserResponse(UserBase):
    """Schema for user response after registration."""
    id: UUID
    email_verified: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Detailed error message")

"""
Changes made to align with User model:
1. Pydantic v2 compatibility:
   - Using ConfigDict instead of deprecated Config class
   - Updated field_validator and model_validator decorators
   - Schema configuration with model_config

2. Improved validation:
   - Strong password requirements with detailed error messages
   - Nickname format validation with specific error messages
   - Email validation using EmailStr

3. Schema organization:
   - Base schema (UserBase) for common attributes
   - Creation schema (UserCreate) with password handling
   - Response schema (UserResponse) for API outputs
   - Error schema (ErrorResponse) for consistent error handling

5. Removed non-registration functionality:
   - Profile fields (bio, URLs)
   - Professional status
   - Login-related fields
   - CRUD operations (UserUpdate, UserListResponse)
   - Auth-related schemas (LoginRequest)
"""
