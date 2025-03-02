import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guest import Guest, GuestStatus


@pytest.mark.asyncio
async def test_create_guest(db_session: AsyncSession):
    """Test guest creation with required fields."""
    new_guest = Guest(session_id="abc123")
    db_session.add(new_guest)
    await db_session.commit()
    await db_session.refresh(new_guest)

    retrieved_guest = await db_session.get(Guest, new_guest.id)
    assert retrieved_guest is not None
    assert retrieved_guest.session_id == "abc123"
    assert retrieved_guest.status == GuestStatus.NEW  # Default status check
    assert isinstance(retrieved_guest.id, uuid.UUID)


@pytest.mark.asyncio
async def test_update_guest_status(db_session: AsyncSession, test_guest: Guest):
    """Test updating the status of a guest."""
    test_guest.status = GuestStatus.CONTACTED
    await db_session.commit()
    await db_session.refresh(test_guest)

    updated_guest = await db_session.get(Guest, test_guest.id)
    assert updated_guest.status == GuestStatus.CONTACTED


@pytest.mark.asyncio
async def test_interaction_history_updates_last_interaction(db_session: AsyncSession, test_guest: Guest):
    """Test that updating interaction history also updates last_interaction.
    
    Instead of using .append(), reassign a new list to trigger the event listener.
    """
    initial_last_interaction = test_guest.last_interaction

    # Create a new history list to trigger the "set" event
    new_event = {"event": "clicked_button", "timestamp": str(datetime.utcnow())}
    new_history = (test_guest.interaction_history or []) + [new_event]
    test_guest.interaction_history = new_history

    await db_session.commit()
    await db_session.refresh(test_guest)

    updated_guest = await db_session.get(Guest, test_guest.id)
    assert updated_guest.last_interaction is not None
    # Ensure the last_interaction has changed; note that if they are extremely close in time, this may require a brief delay.
    assert updated_guest.last_interaction != initial_last_interaction


@pytest.mark.asyncio
async def test_guest_repr(test_guest: Guest):
    """Test the string representation of a guest.
    
    The repr should slice the session_id to its first 8 characters.
    For "test_session_123", that is "test_ses".
    """
    expected_substring = "<Guest Session test_ses, Status: NEW>"
    assert expected_substring in repr(test_guest)


@pytest.mark.asyncio
async def test_guest_with_optional_fields(db_session: AsyncSession):
    """Test guest creation with optional fields."""
    guest = Guest(
        session_id="opt_fields_123",
        name="John Doe",
        company="TechCorp",
        industry="Software",
        contact_info="johndoe@example.com",
        project_type=["Website", "Mobile App"],
        budget="$50,000",
        timeline="6 months",
        status=GuestStatus.CONVERTED,
    )
    db_session.add(guest)
    await db_session.commit()
    await db_session.refresh(guest)

    retrieved_guest = await db_session.get(Guest, guest.id)
    assert retrieved_guest is not None
    assert retrieved_guest.name == "John Doe"
    assert retrieved_guest.company == "TechCorp"
    assert retrieved_guest.project_type == ["Website", "Mobile App"]
    assert retrieved_guest.status == GuestStatus.CONVERTED
