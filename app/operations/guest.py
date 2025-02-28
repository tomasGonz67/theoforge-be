from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.guest import Guest

logger = logging.getLogger(__name__)

class GuestService:
    """Service class for guest-related operations."""
    
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        """Execute a query with error handling and transaction management."""
        try:
            result = await session.execute(query)
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def create_guest(cls, session: AsyncSession, guest_data: Dict[str, Any]) -> Optional[Guest]:
        """Create a new guest record."""
        try:
            guest = Guest(**guest_data)
            session.add(guest)
            await session.commit()
            await session.refresh(guest)
            return guest
        except SQLAlchemyError as e:
            logger.error(f"Error creating guest: {e}")
            await session.rollback()
            return None

    @classmethod
    async def get_all_guests(cls, session: AsyncSession) -> List[Guest]:
        """Retrieve all guests."""
        result = await cls._execute_query(session, select(Guest))
        if result:
            return result.scalars().all()
        return []

    @classmethod
    async def get_guest_by_id(cls, session: AsyncSession, guest_id: UUID) -> Optional[Guest]:
        """Retrieve a guest by ID."""
        result = await cls._execute_query(session, select(Guest).filter(Guest.id == guest_id))
        if result:
            return result.scalar_one_or_none()
        return None

    @classmethod
    async def update_guest(cls, session: AsyncSession, guest: Guest, update_data: Dict[str, Any]) -> Optional[Guest]:
        """Update a guest record."""
        try:
            # Special handling for conversation history to append rather than replace
            if "conversation_history" in update_data:
                existing_history = guest.conversation_history or []
                new_history = update_data["conversation_history"]
                update_data["conversation_history"] = existing_history + new_history

            # Update guest attributes
            for key, value in update_data.items():
                setattr(guest, key, value)

            await session.commit()
            await session.refresh(guest)
            return guest
        except SQLAlchemyError as e:
            logger.error(f"Error updating guest {guest.id}: {e}")
            await session.rollback()
            return None

    @classmethod
    async def delete_guest(cls, session: AsyncSession, guest: Guest) -> bool:
        """Delete a guest record."""
        try:
            await session.delete(guest)
            await session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting guest {guest.id}: {e}")
            await session.rollback()
            return False
