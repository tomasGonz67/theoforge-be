import pytest
from app.models.guest import Guest, GuestStatus

@pytest.mark.asyncio
async def test_guest_model_creation():
    """Test creating a Guest model instance."""
    guest = Guest(
        session_id="test_session",
        page_views=["/home"],
        interaction_events=["clicked_signup"],
        status=GuestStatus.NEW,  # ✅ Fixed field name
        interaction_history=[],
    )

    assert guest.session_id == "test_session"
    assert guest.status == GuestStatus.NEW
    assert isinstance(guest.page_views, list)
    assert isinstance(guest.interaction_events, list)
