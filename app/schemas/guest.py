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
    id: int

    class Config:
        from_attributes = True  # ✅ Updated for Pydantic V2
