from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.operations.guest import GuestService
from app.schemas.guest import GuestCreate, GuestSchema

# Define router with prefix and tags for proper grouping
router = APIRouter(
    prefix="/guests",  # All endpoints will start with /guests
    tags=["Guest"]  # Group all these routes under "guest" in the OpenAPI docs
)

@router.post("/", response_model=GuestSchema)
async def create_guest(guest_data: GuestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new guest entry asynchronously."""
    guest = await GuestService.create_guest(db, guest_data.model_dump(exclude={"id"}))
    if not guest:
        raise HTTPException(status_code=500, detail="Failed to create guest")
    return guest

@router.get("/", response_model=List[GuestSchema])
async def get_guests(db: AsyncSession = Depends(get_db)):
    """Retrieve all guests asynchronously."""
    return await GuestService.get_all_guests(db)

@router.get("/{guest_id}", response_model=GuestSchema)
async def get_guest(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a guest by ID asynchronously."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

@router.put("/{guest_id}", response_model=GuestSchema)
async def update_guest(guest_id: UUID, guest_data: GuestCreate, db: AsyncSession = Depends(get_db)):
    """Update an existing guest while appending to conversation history."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    updated_guest = await GuestService.update_guest(
        db, 
        guest, 
        guest_data.model_dump(exclude_unset=True)
    )
    
    if not updated_guest:
        raise HTTPException(status_code=500, detail="Failed to update guest")
    
    return updated_guest

@router.delete("/{guest_id}")
async def delete_guest(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a guest asynchronously."""
    guest = await GuestService.get_guest_by_id(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    success = await GuestService.delete_guest(db, guest)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete guest")
    
    return {"message": "Guest deleted successfully"}

@router.post("/guests/{guest_id}/chat")
async def update_conversation(guest_id: UUID, message: str, sender: str, db: AsyncSession = Depends(get_db)):
    updated_guest = await GuestService.add_chat_message(db, guest_id, message, sender)
    if updated_guest is None:
        return {"error": "Guest not found or update failed"}
    return {
        "conversation_history": updated_guest.conversation_history,
        "last_interaction": updated_guest.last_interaction
    }

