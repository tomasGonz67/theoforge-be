from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from app.database import get_async_db
from app.models.guest import Guest
from app.schemas.guest import GuestSchema, GuestCreate

router = APIRouter(prefix="/guests", tags=["Guests"])

async def get_all_guests(db: AsyncSession):
    """Retrieve all guests asynchronously."""
    result = await db.execute(select(Guest))
    return result.scalars().all()

async def get_guest(db: AsyncSession, guest_id: uuid.UUID):
    """Retrieve a single guest by ID asynchronously."""
    result = await db.execute(select(Guest).where(Guest.id == guest_id))
    return result.scalars().one_or_none()

@router.get("/", response_model=List[GuestSchema])
async def fetch_all_guests(db: AsyncSession = Depends(get_async_db)):
    """Retrieve all guests asynchronously."""
    return await get_all_guests(db)

@router.get("/{guest_id}", response_model=GuestSchema)
async def fetch_guest(guest_id: uuid.UUID, db: AsyncSession = Depends(get_async_db)):
    """Retrieve a guest by ID asynchronously."""
    guest = await get_guest(db, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

@router.post("/", response_model=GuestSchema)
async def add_guest(guest_data: GuestCreate, db: AsyncSession = Depends(get_async_db)):
    """Create a new guest entry asynchronously."""
    guest = Guest(
        id=uuid.uuid4(),
        **guest_data.dict(exclude_unset=True)
    )
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest
