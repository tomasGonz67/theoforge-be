from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.operations.guest import GuestService
from app.schemas.guest import GuestCreate, GuestSchema, GuestUpdate

# Define router with prefix and tags for proper grouping
router = APIRouter(
    prefix="/guests",  # All endpoints will start with /guests
    tags=["Guest"]  # Group all these routes under "Guest" in OpenAPI docs
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

@router.get("/{session_id}", response_model=GuestSchema)
async def get_guest(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a guest by session ID asynchronously."""
    guest = await GuestService.get_guest_by_session(db, session_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

@router.put("/{session_id}", response_model=GuestSchema)
async def update_guest(session_id: str, guest_data: GuestUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing guest with engagement tracking."""
    guest = await GuestService.get_guest_by_session(db, session_id)
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

@router.delete("/{session_id}")
async def delete_guest(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a guest asynchronously."""
    guest = await GuestService.get_guest_by_session(db, session_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    success = await GuestService.delete_guest(db, guest)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete guest")
    
    return {"message": "Guest deleted successfully"}

@router.post("/{session_id}/interactions")
async def add_interaction(session_id: str, event: dict, db: AsyncSession = Depends(get_db)):
    """Append an interaction event to the guest's record."""
    updated_guest = await GuestService.add_interaction(db, session_id, event)
    if updated_guest is None:
        raise HTTPException(status_code=404, detail="Guest not found or update failed")
    
    return {
        "interaction_history": updated_guest.interaction_history,
        "last_interaction": updated_guest.last_interaction
    }
