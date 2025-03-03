import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.operations.guest import GuestService
from app.models.guest import Guest, GuestStatus
from app.schemas.guest import GuestCreate, GuestUpdate, GuestSchema, ErrorResponse

@pytest.mark.asyncio
async def test_create_guest_schema():
    """Test the GuestCreate schema."""
    guest_data = {
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
    guest = GuestCreate(**guest_data)
    assert guest.session_id == "session_test123"
    assert guest.status == GuestStatus.NEW

@pytest.mark.asyncio
async def test_update_guest_schema():
    """Test the GuestUpdate schema."""
    update_data = {
        "page_views": ["/home", "/products", "/checkout"],
        "interaction_events": ["clicked_purchase"],
        "status": "CONTACTED",
        "interaction_history": [{"event": "completed_purchase", "timestamp": "2025-03-02T10:00:00Z"}]
    }
    update_guest = GuestUpdate(**update_data)
    assert update_guest.status == GuestStatus.CONTACTED
    assert "clicked_purchase" in update_guest.interaction_events

@pytest.mark.asyncio
async def test_guest_schema():
    """Test the GuestSchema schema."""
    guest_data = {
        "id": uuid4(),
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
        "status": "NEW",
        "first_visit_timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    guest = GuestSchema(**guest_data)
    assert guest.id is not None
    assert guest.status == GuestStatus.NEW
    assert guest.first_visit_timestamp is not None

@pytest.mark.asyncio
async def test_error_response_schema():
    """Test the ErrorResponse schema."""
    error_data = {
        "error": "GuestNotFound",
        "details": "The guest with the provided session ID does not exist."
    }
    error_response = ErrorResponse(**error_data)
    assert error_response.error == "GuestNotFound"
    assert error_response.details == "The guest with the provided session ID does not exist."