from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID

from app.models.user import UserRole, SubscriptionPlan

class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr = Field(..., description="User's email address")
    nickname: Optional[str] = Field(None, description="User's nickname")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    role: UserRole

class UserCreate(BaseModel):
    """Schema for user registration with password validation."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    nickname: Optional[str] = Field(None, description="User's nickname")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 9:
            raise ValueError("Password must be at least 9 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserUpdate(BaseModel):
    """Schema for user profile update."""
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    card_number: Optional[str] = None
    ccv: Optional[str] = None
    security_code: Optional[str] = None
    subscription_plan: Optional[str] = None

    @field_validator("subscription_plan")
    @classmethod
    def validate_subscription_plan(cls, v: Optional[str]) -> Optional[str]:
        """Ensure subscription_plan is one of the valid options."""
        if v is not None:
            valid_plans = {plan.name for plan in SubscriptionPlan}
            if v.upper() not in valid_plans:
                raise ValueError("Invalid subscription plan")
            return v.upper()
        return v

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
