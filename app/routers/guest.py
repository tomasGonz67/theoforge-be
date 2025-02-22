from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.guest import GuestCreate, GuestOut, GuestUpdate
from app.crud.guest import get_guest, get_guests, create_guest, update_guest, delete_guest
from app.database.session import SessionLocal

router = APIRouter(prefix="/guests", tags=["Guests"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=GuestOut)
def create_new_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    return create_guest(db, guest)

@router.get("/{guest_id}", response_model=GuestOut)
def read_guest(guest_id: int, db: Session = Depends(get_db)):
    return get_guest(db, guest_id)

@router.get("/", response_model=List[GuestOut])
def read_guests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_guests(db, skip=skip, limit=limit)

@router.put("/{guest_id}", response_model=GuestOut)
def update_existing_guest(guest_id: int, guest_update: GuestUpdate, db: Session = Depends(get_db)):
    return update_guest(db, guest_id, guest_update)

@router.delete("/{guest_id}", response_model=GuestOut)
def delete_existing_guest(guest_id: int, db: Session = Depends(get_db)):
    return delete_guest(db, guest_id)
