import pytest
from app.models.guest import GuestStatus
from app.schemas.guest import GuestCreate, GuestSchema
from datetime import datetime
from uuid import uuid4

@pytest.mark.asyncio
async def test_guest_create_schema():
    """Test creating a GuestCreate schema."""
    guest_data = GuestCreate(
        session_id="test_session",
        page_views=["/home"],
        interaction_events=["clicked_signup"],
        status=GuestStatus.NEW,  # ✅ Fixed field name
        interaction_history=[],
    )

    assert guest_data.session_id == "test_session"
    assert guest_data.status == GuestStatus.NEW
    assert isinstance(guest_data.page_views, list)
    assert isinstance(guest_data.interaction_events, list)

@pytest.mark.asyncio
async def test_guest_schema():
    """Test creating a GuestSchema."""
    guest_data = GuestSchema(
        id=uuid4(),
        session_id="test_session",
        page_views=["/home"],
        interaction_events=["clicked_signup"],
        status=GuestStatus.NEW,  # ✅ Fixed field name
        interaction_history=[],
        first_visit_timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert guest_data.session_id == "test_session"
    assert guest_data.status == GuestStatus.NEW
    assert isinstance(guest_data.page_views, list)
    assert isinstance(guest_data.interaction_events, list)
