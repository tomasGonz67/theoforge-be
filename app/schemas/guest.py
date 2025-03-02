from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, UUID4
from app.models.guest import GuestStatus

class GuestBase(BaseModel):
    """Base schema for Guest with common attributes."""
    session_id: str = Field(..., description="Guest's session identifier", example="session_abc123")
    page_views: Optional[List[str]] = Field(
        default=["/home", "/about"], description="List of page views", example=["/home", "/products"]
    )
    interaction_events: Optional[List[str]] = Field(
        default=["clicked_signup"], description="List of interaction events", example=["clicked_login", "viewed_product"]
    )
    status: GuestStatus = Field(
        default=GuestStatus.NEW, description="Guest status", example="NEW"
    )
    interaction_history: Optional[List[Dict[str, str]]] = Field(
        default=[{"event": "visited_homepage", "timestamp": "2025-03-01T12:00:00Z"}], 
        description="List of past interactions",
        example=[{"event": "clicked_signup", "timestamp": "2025-03-01T14:00:00Z"}]
    )

class GuestCreate(GuestBase):
    """Schema for creating a new guest entry."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "session_test123",
                "page_views": ["/home", "/contact"],
                "interaction_events": ["clicked_contact_form"],
                "status": "NEW",
                "interaction_history": [{"event": "filled_contact_form", "timestamp": "2025-03-01T15:30:00Z"}]
            }
        }
    }

class GuestUpdate(BaseModel):
    """Schema for updating a guest entry."""
    page_views: Optional[List[str]] = Field(
        default=None, description="Updated list of page views", example=["/home", "/products", "/checkout"]
    )
    interaction_events: Optional[List[str]] = Field(
        default=None, description="Updated list of interaction events", example=["clicked_purchase"]
    )
    status: Optional[GuestStatus] = Field(
        default=None, description="Updated guest status", example="CONTACTED"
    )
    interaction_history: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Updated list of past interactions",
        example=[{"event": "completed_purchase", "timestamp": "2025-03-02T10:00:00Z"}]
    )

class GuestSchema(GuestBase):
    """Schema for returning a guest object."""
    id: UUID4 = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    first_visit_timestamp: datetime = Field(
        ..., description="Timestamp of the first visit", example="2025-03-01T12:00:00Z"
    )
    created_at: datetime = Field(..., example="2025-03-01T12:05:00Z")
    updated_at: datetime = Field(..., example="2025-03-01T12:10:00Z")

class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type", example="GuestNotFound")
    details: Optional[str] = Field(None, description="Detailed error message", example="The guest with the provided session ID does not exist.")
