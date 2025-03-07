from pydantic import BaseModel
from typing import List, Optional
import uuid


class ResourceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    tags: Optional[list] = None
    profile_picture: Optional[str] = None
    source_url: Optional[str] = None
    user_id: uuid.UUID
    is_public: bool


class ResourceCreateSchema(ResourceBase):
    """Schema for creating a new resource"""
    pass


class ResourceUpdateSchema(BaseModel):
    """Schema for updating a resource"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list] = None
    profile_picture: Optional[str] = None
    source_url: Optional[str] = None
    is_public: Optional[bool] = None


class ResourceSchema(ResourceBase):
    """Schema for returning a resource with related resources"""
    id: uuid.UUID
    related_resources: List["ResourceSchema"] = []

    class Config:
        orm_mode = True
