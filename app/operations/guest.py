from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from app.models.guest import Guest, GuestStatus

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
    async def get_guest_by_session(cls, session: AsyncSession, session_id: str) -> Union[Guest, List[Guest], None]:
        """Retrieve guest(s) by session ID (handles multiple results)."""
        result = await cls._execute_query(session, select(Guest).filter(Guest.session_id == session_id))
        
        if not result:
            return None

        guests = result.scalars().all()

        if len(guests) == 1:
            return guests[0]
        elif len(guests) > 1:
            return guests  # Return all guests if multiple exist
        return None

    @classmethod
    async def update_guest(cls, session: AsyncSession, guest: Guest, update_data: Dict[str, Any]) -> Optional[Guest]:
        """Update an existing guest record."""
        try:
            for key, value in update_data.items():
                setattr(guest, key, value)
            guest.updated_at = datetime.utcnow()
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