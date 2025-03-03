from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, UUID4, ConfigDict

from app.models.guest import GuestStatus

class GuestBase(BaseModel):
    """Base schema for Guest with common attributes."""
    session_id: str = Field(..., description="Guest's session identifier")
    page_views: Optional[List[str]] = Field(
        default=["/home", "/about"], 
        description="List of page views"
    )
    interaction_events: Optional[List[str]] = Field(
        default=["clicked_signup"], 
        description="List of interaction events"
    )
    name: Optional[str] = Field(None, description="Guest's full name")
    company: Optional[str] = Field(None, description="Company associated with the guest")
    industry: Optional[str] = Field(None, description="Industry of the guest")
    project_type: Optional[List[str]] = Field(None, description="Type of project guest is interested in")
    budget: Optional[str] = Field(None, description="Estimated budget for the project")
    timeline: Optional[str] = Field(None, description="Project timeline")
    contact_info: Optional[str] = Field(None, description="Guest's contact information")
    pain_points: Optional[List[str]] = Field(None, description="Challenges or problems the guest is facing")
    current_tech: Optional[List[str]] = Field(None, description="Guest's current technology stack")
    additional_notes: Optional[str] = Field(None, description="Any additional notes")
    interaction_history: Optional[List[Dict[str, str]]] = Field(
        default=[{"event": "visited_homepage", "timestamp": "2025-03-01T12:00:00Z"}], 
        description="List of past interactions"
    )
    status: GuestStatus = Field(
        default=GuestStatus.NEW, description="Current status of the guest: NEW, CONTACTED, or CONVERTED"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_abc123",
                "page_views": ["/home", "/products"],
                "interaction_events": ["clicked_login", "viewed_product"],
                "interaction_history": [{"event": "clicked_signup", "timestamp": "2025-03-01T14:00:00Z"}]
            }
        }
    )

class GuestCreate(GuestBase):
    """Schema for creating a new guest entry."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_test123",
                "page_views": ["/home", "/contact"],
                "interaction_events": ["clicked_contact_form"],
                "name": "John Doe",
                "company": "Tech Solutions",
                "industry": "Software",
                "project_type": ["Web Development"],
                "budget": "$10,000 - $20,000",
                "timeline": "Q2 2025",
                "contact_info": "john.doe@example.com",
                "pain_points": ["Scalability issues", "Need for automation"],
                "current_tech": ["React", "Node.js"],
                "additional_notes": "Looking for a long-term partnership",
                "interaction_history": [{"event": "filled_contact_form", "timestamp": "2025-03-01T15:30:00Z"}],
                "status": "NEW"
            }
        }
    )

class GuestUpdate(BaseModel):
    """Schema for updating a guest entry."""
    page_views: Optional[List[str]] = Field(
        default=None, 
        description="Updated list of page views"
    )
    interaction_events: Optional[List[str]] = Field(
        default=None, 
        description="Updated list of interaction events"
    )
    status: Optional[GuestStatus] = Field(
        default=None, 
        description="Updated guest status"
    )
    interaction_history: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Updated list of past interactions"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page_views": ["/home", "/products", "/checkout"],
                "interaction_events": ["clicked_purchase"],
                "status": "CONTACTED",
                "interaction_history": [{"event": "completed_purchase", "timestamp": "2025-03-02T10:00:00Z"}]
            }
        }
    )

class GuestSchema(GuestBase):
    """Schema for returning a guest object."""
    id: UUID4 = Field(...) 
    first_visit_timestamp: datetime = Field(
        ..., 
        description="Timestamp of the first visit"
    )
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "first_visit_timestamp": "2025-03-01T12:00:00Z",
                "created_at": "2025-03-01T12:05:00Z",
                "updated_at": "2025-03-01T12:10:00Z"
            }
        }
    )

class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Detailed error message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "GuestNotFound",
                "details": "The guest with the provided session ID does not exist."
            }
        }
    )