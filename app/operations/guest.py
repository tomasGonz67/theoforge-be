from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
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
        """Create a new guest record with an anonymous session ID."""
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
        """Retrieve all guest records."""
        result = await cls._execute_query(session, select(Guest))
        if result:
            return result.scalars().all()
        return []

    @classmethod
    async def get_guest_by_session(cls, session: AsyncSession, session_id: str) -> Optional[Guest]:
        """Retrieve a guest by session ID."""
        result = await cls._execute_query(session, select(Guest).filter(Guest.session_id == session_id))
        if result:
            return result.scalar_one_or_none()
        return None

    @classmethod
    async def update_guest(cls, session: AsyncSession, guest: Guest, update_data: Dict[str, Any]) -> Optional[Guest]:
        """Update a guest record with privacy-focused engagement tracking."""
        try:
            # Append new page views and interactions instead of replacing them
            if "page_views" in update_data:
                existing_views = guest.page_views or []
                new_views = update_data["page_views"]
                update_data["page_views"] = list(set(existing_views + new_views))  # Avoid duplicates

            if "interaction_events" in update_data:
                existing_events = guest.interaction_events or []
                new_events = update_data["interaction_events"]
                update_data["interaction_events"] = existing_events + new_events

            # Special handling for interaction history
            if "interaction_history" in update_data:
                existing_history = guest.interaction_history or []
                new_history = update_data["interaction_history"]
                update_data["interaction_history"] = existing_history + new_history

            # Update guest attributes
            for key, value in update_data.items():
                setattr(guest, key, value)

            guest.last_interaction = datetime.utcnow()

            await session.commit()
            await session.refresh(guest)
            return guest
        except SQLAlchemyError as e:
            logger.error(f"Error updating guest {guest.session_id}: {e}")
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
            logger.error(f"Error deleting guest {guest.session_id}: {e}")
            await session.rollback()
            return False

    @classmethod
    async def add_interaction(cls, session: AsyncSession, session_id: str, event: Dict[str, Any]) -> Optional[Guest]:
        """Append an interaction event to the guest's record and update last interaction."""
        guest = await cls.get_guest_by_session(session, session_id)
        if not guest:
            logger.error(f"Guest session {session_id} not found.")
            return None
        
        try:
            guest.interaction_history = (guest.interaction_history or []) + [event]
            guest.last_interaction = datetime.utcnow()

            await session.commit()
            await session.refresh(guest)
            return guest
        except SQLAlchemyError as e:
            logger.error(f"Error updating interaction history for guest session {session_id}: {e}")
            await session.rollback()
            return None
