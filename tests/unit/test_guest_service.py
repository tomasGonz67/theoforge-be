import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.operations.guest import GuestService
from app.models.guest import Guest, GuestStatus

@pytest.mark.asyncio
async def test_create_guest(db_session: AsyncSession):
    """Test creating a new guest record."""
    guest_data = {
        "session_id": "test_session_1234",
        "page_views": ["/home", "/about"],
        "interaction_events": ["clicked_signup"],
        "status": GuestStatus.NEW,
        "interaction_history": [{"event": "visited_homepage", "timestamp": "2025-03-01T12:00:00Z"}],
    }
    guest = await GuestService.create_guest(db_session, guest_data)
    assert guest is not None
    assert guest.session_id == "test_session_1234"
    assert guest.status == GuestStatus.NEW

@pytest.mark.asyncio
async def test_get_guest_by_id(db_session: AsyncSession, test_guest: Guest):
    """Test retrieving a guest by ID."""
    guest = await GuestService.get_guest_by_id(db_session, test_guest.id)
    assert guest is not None
    assert guest.id == test_guest.id

@pytest.mark.asyncio
async def test_get_guest_by_session(db_session: AsyncSession, test_guest: Guest):
    """Test retrieving a guest by session ID."""
    guest = await GuestService.get_guest_by_session(db_session, test_guest.session_id)
    assert guest is not None
    assert guest.session_id == test_guest.session_id

@pytest.mark.asyncio
async def test_update_guest(db_session: AsyncSession, test_guest: Guest):
    """Test updating a guest's information."""
    update_data = {"status": GuestStatus.CONTACTED}
    updated_guest = await GuestService.update_guest(db_session, test_guest, update_data)
    assert updated_guest is not None
    assert updated_guest.status == GuestStatus.CONTACTED

@pytest.mark.asyncio
async def test_delete_guest(db_session: AsyncSession, test_guest: Guest):
    """Test deleting a guest record."""
    result = await GuestService.delete_guest(db_session, test_guest)
    assert result is True
    deleted_guest = await GuestService.get_guest_by_id(db_session, test_guest.id)
    assert deleted_guest is None

@pytest.mark.asyncio
async def test_add_chat_message(db_session: AsyncSession, test_guest: Guest):
    """Test appending a chat message to the guest's interaction history."""
    message = "Hello, how can I help you?"
    sender = "agent"
    updated_guest = await GuestService.add_chat_message(db_session, test_guest.id, message, sender)
    assert updated_guest is not None
    assert updated_guest.interaction_history[-1]["message"] == message
    assert updated_guest.interaction_history[-1]["sender"] == sender