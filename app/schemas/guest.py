from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.guest import GuestEngagementStatus


class GuestBase(BaseModel):
    """Base schema for Guest with common attributes."""
    session_id: str = Field(..., description="Anonymized session identifier for tracking guest interactions")
    page_views: Optional[List[str]] = Field(None, description="List of pages the guest has visited")
    interaction_events: Optional[List[str]] = Field(None, description="List of guest interaction events (e.g., clicks, form submissions)")
    interaction_history: Optional[List[Dict[str, str]]] = Field(None, description="History of guest interactions")
    engagement_status: Optional[GuestEngagementStatus] = Field(
        default=GuestEngagementStatus.NEW_VISITOR,
        description="Engagement status of the guest: NEW_VISITOR, ENGAGED, or RETURNING"
    )

    model_config = ConfigDict(from_attributes=True)


class GuestCreate(GuestBase):
    """Schema for creating a new guest entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc123xyz",
                "page_views": ["/home", "/products", "/contact"],
                "interaction_events": ["clicked_signup", "filled_form"],
                "interaction_history": [{"timestamp": "2025-02-28T14:30:00Z", "event": "Visited homepage"}],
                "engagement_status": "NEW_VISITOR"
            }
        }
    )


class GuestUpdate(BaseModel):
    """Schema for updating a guest entry."""
    page_views: Optional[List[str]] = Field(None, description="Updated list of pages the guest has visited")
    interaction_events: Optional[List[str]] = Field(None, description="Updated list of interaction events")
    interaction_history: Optional[List[Dict[str, str]]] = Field(None, description="Updated interaction history")
    engagement_status: Optional[GuestEngagementStatus] = Field(None, description="Updated engagement status")


class GuestSchema(GuestBase):
    """Schema for returning a guest object."""
    first_visit_timestamp: datetime = Field(..., description="Timestamp of the first visit by the guest")
    last_interaction: Optional[datetime] = Field(None, description="Timestamp of the last recorded interaction")
    created_at: datetime = Field(..., description="Timestamp when the guest record was created")
    updated_at: datetime = Field(..., description="Timestamp when the guest record was last updated")


class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Detailed error message")
