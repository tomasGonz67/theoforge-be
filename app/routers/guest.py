from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestSchema

# Define router with prefix and tags for proper grouping
router = APIRouter(
    prefix="/guests",  # All endpoints will start with /guests
    tags=["Guest"]  # Group all these routes under "guest" in the OpenAPI docs
)

@router.post("/", response_model=GuestSchema)
async def create_guest(guest_data: GuestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new guest entry asynchronously."""
    guest_dict = guest_data.dict(exclude={"id"})  # Ensure no duplicate 'id' key
    guest = Guest(**guest_dict)  # SQLAlchemy model
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest

@router.get("/", response_model=List[GuestSchema])
async def get_guests(db: AsyncSession = Depends(get_db)):
    """Retrieve all guests asynchronously."""
    result = await db.execute(select(Guest))
    return result.scalars().all()

@router.get("/{guest_id}", response_model=GuestSchema)
async def get_guest(guest_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a guest by ID asynchronously."""
    result = await db.execute(select(Guest).filter(Guest.id == guest_id))
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

@router.put("/{guest_id}", response_model=GuestSchema)
async def update_guest(guest_id: str, guest_data: GuestCreate, db: AsyncSession = Depends(get_db)):
    """Update an existing guest while appending to conversation history."""
    result = await db.execute(select(Guest).filter(Guest.id == guest_id))
    guest = result.scalar_one_or_none()
    
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    update_data = guest_data.dict(exclude_unset=True)

    # Append new conversation history instead of overwriting
    if "conversation_history" in update_data:
        existing_history = guest.conversation_history or []
        new_history = update_data["conversation_history"]
        update_data["conversation_history"] = existing_history + new_history

    # Update guest attributes
    for key, value in update_data.items():
        setattr(guest, key, value)

    await db.commit()
    await db.refresh(guest)
    return guest

@router.delete("/{guest_id}")
async def delete_guest(guest_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a guest asynchronously."""
    result = await db.execute(select(Guest).filter(Guest.id == guest_id))
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    await db.delete(guest)
    await db.commit()
    return {"message": "Guest deleted successfully"}
