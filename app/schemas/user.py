# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from faker import Faker

# Initialize Faker
fake = Faker()

class UserBase(BaseModel):
    username: str = Field(..., example=fake.user_name())  # Random username
    email: EmailStr = Field(..., example=fake.email())  # Random email
    full_name: Optional[str] = Field(default=None, example=fake.name())  # Random full name

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserOut(UserBase):
    id: str  # Ensure ID is a string for USER-XXXX format

    class Config:
        from_attributes = True  # For Pydantic V2
