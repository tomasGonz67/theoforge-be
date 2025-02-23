# app/schemas/guest.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class GuestBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class GuestOut(GuestBase):
    id: str  # Use custom Guest ID format like GUEST-4821

    class Config:
        from_attributes = True  # For Pydantic V2
