from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Union
from uuid import UUID

from app.database import get_db
from app.operations.guest import GuestService
from app.schemas.guest import GuestCreate, GuestSchema, GuestUpdate

router = APIRouter(
    prefix="/guests",
    tags=["Guest"]
)

@router.post("/", response_model=GuestSchema)
async def create_guest(guest_data: GuestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new guest entry asynchronously."""
    guest = await GuestService.create_guest(db, guest_data.model_dump(exclude={"id"}))
    if not guest:
        raise HTTPException(status_code=500, detail="Failed to create guest")
    return guest

@router.get("/", response_model=List[GuestSchema])
async def get_all_guests(db: AsyncSession = Depends(get_db)):
    """Retrieve all guests asynchronously."""
    return await GuestService.get_all_guests(db)

@router.get("/{guest_id}", response_model=GuestSchema)
async def get_guest_by_id(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a guest by ID asynchronously."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

@router.get("/session/{session_id}", response_model=List[GuestSchema])
async def get_guest_by_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve guest(s) by session ID."""
    guests = await GuestService.get_guest_by_session(db, session_id)
    if not guests:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guests if isinstance(guests, list) else [guests]

@router.put("/{guest_id}", response_model=GuestSchema)
async def update_guest_by_id(guest_id: UUID, guest_update: GuestUpdate, db: AsyncSession = Depends(get_db)):
    """Update a guest's details asynchronously by guest ID."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    updated_guest = await GuestService.update_guest(db, guest, guest_update.model_dump(exclude_unset=True))
    if not updated_guest:
        raise HTTPException(status_code=500, detail="Failed to update guest")
    return updated_guest

@router.put("/session/{session_id}", response_model=GuestSchema)
async def update_guest_by_session(session_id: str, guest_update: GuestUpdate, db: AsyncSession = Depends(get_db)):
    """Update a guest's details asynchronously by session ID."""
    guest = await GuestService.get_guest_by_session(db, session_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    if isinstance(guest, list):
        raise HTTPException(status_code=400, detail="Multiple guests found for this session ID. Please update individually by ID.")
    updated_guest = await GuestService.update_guest(db, guest, guest_update.model_dump(exclude_unset=True))
    if not updated_guest:
        raise HTTPException(status_code=500, detail="Failed to update guest")
    return updated_guest

@router.delete("/{guest_id}")
async def delete_guest_by_id(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a guest asynchronously by ID."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    success = await GuestService.delete_guest(db, guest)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete guest")
    return {"message": "Guest deleted successfully"}

@router.delete("/session/{session_id}")
async def delete_guest_by_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a guest asynchronously by session ID."""
    guests = await GuestService.get_guest_by_session(db, session_id)
    if not guests:
        raise HTTPException(status_code=404, detail="Guest not found")
    if isinstance(guests, list):
        raise HTTPException(status_code=400, detail="Multiple guests found for this session ID. Please delete individually by ID.")
    success = await GuestService.delete_guest(db, guests)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete guest")
    return {"message": "Guest deleted successfully"}

@router.post("/{guest_id}/chat")
async def update_conversation(guest_id: UUID, message: str, sender: str, db: AsyncSession = Depends(get_db)):
    """Append a message to a guest's conversation history."""
    updated_guest = await GuestService.add_chat_message(db, guest_id, message, sender)
    if updated_guest is None:
        raise HTTPException(status_code=404, detail="Guest not found or update failed")
    return {
        "conversation_history": updated_guest.interaction_history,
        "last_interaction": updated_guest.last_interaction
    }
