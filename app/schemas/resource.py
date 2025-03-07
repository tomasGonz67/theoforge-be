import uuid
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ResourceBase(BaseModel):
    """Base schema for a resource."""
    name: str = "Sample Resource"
    description: Optional[str] = "This is a sample description of the resource."
    category: str = "Technology"
    tags: Optional[Dict[str, str]] = {"topic": "AI", "level": "Beginner"}  # Example tags
    profile_picture: Optional[str] = "https://example.com/sample-profile.jpg"  # Example URL
    source_url: Optional[str] = "https://example.com/resource-info"  # Example URL
    is_public: bool = True

class ResourceCreate(ResourceBase):
    """Schema for creating a new resource."""
    pass

class ResourceUpdate(BaseModel):
    """Schema for updating a resource (all fields optional)."""
    name: Optional[str] = "Updated Resource"
    description: Optional[str] = "Updated description."
    category: Optional[str] = "Data Science"
    tags: Optional[Dict[str, str]] = {"topic": "Machine Learning", "difficulty": "Intermediate"}
    profile_picture: Optional[str] = "https://example.com/updated-profile.jpg"
    source_url: Optional[str] = "https://example.com/updated-resource"
    is_public: Optional[bool] = None

class ResourceOut(ResourceBase):
    """Schema for returning resource data."""
    id: uuid.UUID = uuid.uuid4()
    user_id: uuid.UUID = uuid.uuid4()
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    related_resources: List[uuid.UUID] = [uuid.uuid4(), uuid.uuid4()]  # Example related resources

    class Config:
        from_attributes = True  # Ensures compatibility with SQLAlchemy models

class ResourceLink(BaseModel):
    """Schema for linking two resources."""
    related_resource_id: uuid.UUID = uuid.uuid4()
