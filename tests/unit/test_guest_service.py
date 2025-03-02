import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guest import Guest
from app.operations.guest import GuestService

@pytest.mark.asyncio
async def test_create_guest(db_session: AsyncSession):
    """Unit test for creating a guest using GuestService."""
    guest_data = {
        "session_id": "unit_test_session",
        "page_views": ["/unit", "/test"],
        "interaction_events": ["clicked_unit_test"],
        "status": "NEW",
        "interaction_history": [{"event": "unit_test", "timestamp": "2025-03-01T12:00:00Z"}],
    }

    guest = await GuestService.create_guest(db_session, guest_data)
    assert guest is not None
    assert guest.session_id == "unit_test_session"

@pytest.mark.asyncio
async def test_get_guest_by_session(db_session: AsyncSession, test_guest):
    """Unit test for retrieving a guest by session ID."""
    guest = await GuestService.get_guest_by_session(db_session, test_guest.session_id)
    assert guest is not None
    assert guest.session_id == test_guest.session_id
