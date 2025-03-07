import uuid
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

class ResourceBase(BaseModel):
    """Base schema for a resource."""
    name: str
    description: Optional[str] = None
    category: str
    tags: Optional[Dict[str, str]] = None  # JSON field for storing key-value tags
    profile_picture: Optional[HttpUrl] = None  # URL validation
    source_url: Optional[HttpUrl] = None
    is_public: bool = True

class ResourceCreate(ResourceBase):
    """Schema for creating a new resource."""
    pass

class ResourceUpdate(BaseModel):
    """Schema for updating a resource (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    profile_picture: Optional[HttpUrl] = None
    source_url: Optional[HttpUrl] = None
    is_public: Optional[bool] = None

class ResourceOut(ResourceBase):
    """Schema for returning resource data."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    related_resources: List[uuid.UUID] = []  # List of related resource IDs

    class Config:
        from_attributes = True  # Ensures compatibility with ORM models

class ResourceLink(BaseModel):
    """Schema for linking two resources."""
    related_resource_id: uuid.UUID
