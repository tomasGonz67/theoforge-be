from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, UUID4, ConfigDict


class GuestBase(BaseModel):
    """Base schema for Guest with common attributes."""
    name: str = Field(..., description="Guest's full name")
    company: Optional[str] = Field(None, description="Company associated with the guest")
    industry: Optional[str] = Field(None, description="Industry of the guest")
    project_type: Optional[List[str]] = Field(None, description="Type of project guest is interested in")
    budget: Optional[str] = Field(None, description="Estimated budget for the project")
    timeline: Optional[str] = Field(None, description="Project timeline")
    contact_info: Optional[str] = Field(None, description="Guest's contact information")
    pain_points: Optional[List[str]] = Field(None, description="Challenges or problems the guest is facing")
    current_tech: Optional[List[str]] = Field(None, description="Guest's current technology stack")
    additional_notes: Optional[str] = Field(None, description="Any additional notes")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="List of past conversations with the guest")

    model_config = ConfigDict(from_attributes=True)


class GuestCreate(GuestBase):
    """Schema for creating a new guest entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "conversation_history": [{"date": "2025-02-28", "summary": "Discussed project scope"}]
            }
        }
    )


class GuestSchema(GuestBase):
    """Schema for returning a guest object."""
    id: UUID4
    first_contact_timestamp: datetime = Field(..., description="Timestamp of the first contact with the guest")
    created_at: datetime = Field(..., description="Timestamp when the guest record was created")
    updated_at: datetime = Field(..., description="Timestamp when the guest record was last updated")


class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Detailed error message")
