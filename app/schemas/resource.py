from pydantic import BaseModel, Field, UUID4, HttpUrl
from typing import List, Optional
import uuid


class ResourceBase(BaseModel):
    """Base schema for a resource with common attributes."""
    name: str = Field(..., description="Name of the resource")
    description: Optional[str] = Field(None, description="Detailed description of the resource")
    category: str = Field(..., description="Category of the resource")
    tags: Optional[List[str]] = Field(default=[], description="List of associated tags")
    profile_picture: Optional[str] = Field(None, description="URL to the resource's profile picture")
    source_url: Optional[str] = Field(None, description="External source URL for the resource")
    user_id: UUID4 = Field(..., description="ID of the user who created the resource")
    is_public: bool = Field(..., description="Visibility status of the resource")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Python Best Practices",
                "description": "A guide on Python coding standards",
                "category": "Programming",
                "tags": ["Python", "Best Practices", "Coding"],
                "profile_picture": "https://example.com/python.png",
                "source_url": "https://example.com/python-guide",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "is_public": True
            }
        }
    }


class ResourceCreateSchema(ResourceBase):
    """Schema for creating a new resource."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "FastAPI for Beginners",
                "description": "A complete guide to FastAPI with best practices.",
                "category": "Development",
                "tags": ["FastAPI", "Python", "API"],
                "profile_picture": "https://example.com/fastapi.png",
                "source_url": "https://example.com/fastapi-guide",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "is_public": True
            }
        }
    }


class ResourceUpdateSchema(BaseModel):
    """Schema for updating a resource."""
    name: Optional[str] = Field(None, description="Updated name of the resource")
    description: Optional[str] = Field(None, description="Updated description")
    category: Optional[str] = Field(None, description="Updated category")
    tags: Optional[List[str]] = Field(None, description="Updated list of tags")
    profile_picture: Optional[HttpUrl] = Field(None, description="Updated profile picture URL")
    source_url: Optional[HttpUrl] = Field(None, description="Updated source URL")
    is_public: Optional[bool] = Field(None, description="Updated visibility status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Advanced FastAPI Guide",
                "description": "A deep dive into FastAPI's advanced features.",
                "category": "Development",
                "tags": ["FastAPI", "Python", "Advanced"],
                "profile_picture": "https://example.com/advanced-fastapi.png",
                "source_url": "https://example.com/advanced-fastapi-guide",
                "is_public": False
            }
        }
    }


class ResourceSchema(ResourceBase):
    """Schema for returning a resource with related resources."""
    id: UUID4 = Field(..., description="Unique identifier of the resource")
    related_resources: List["ResourceSchema"] = Field(default=[], description="List of related resources")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "FastAPI Guide",
                "description": "A beginner-friendly guide to FastAPI",
                "category": "Education",
                "tags": ["FastAPI", "Python", "API"],
                "profile_picture": "https://example.com/fastapi.png",
                "source_url": "https://example.com/resource",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_public": True,
                "related_resources": [
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "name": "Async in Python",
                        "description": "Understanding async programming in Python",
                        "category": "Education",
                        "tags": ["Async", "Python", "Concurrency"],
                        "profile_picture": "https://example.com/async.png",
                        "source_url": "https://example.com/async",
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "is_public": True,
                        "related_resources": []
                    }
                ]
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Detailed error message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ResourceNotFound",
                "details": "The requested resource does not exist."
            }
        }
    }
