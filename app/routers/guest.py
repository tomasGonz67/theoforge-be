# app/routers/guest.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import random
from faker import Faker

from app.schemas.guest import GuestCreate, GuestOut, GuestUpdate
from app.crud.guest import get_guest, get_guests, create_guest, update_guest, delete_guest
from app.database.session import SessionLocal

router = APIRouter(prefix="/guests", tags=["Guests"])

# Initialize Faker
fake = Faker()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to generate unique guest ID
def generate_unique_guest_id():
    return f"GUEST-{random.randint(1000, 9999)}"

@router.post("/", response_model=GuestOut)
def create_new_guest(
    guest: GuestCreate = Body(
        ...,
        example={
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number()
        }
    ),
    db: Session = Depends(get_db)
):
    # Auto-generate fields if empty
    if not guest.name.strip():
        guest.name = fake.name()

    if not guest.email.strip():
        guest.email = fake.email()

    if not guest.phone or not guest.phone.strip():
        guest.phone = fake.phone_number()

    # Assign unique guest ID
    guest_id = generate_unique_guest_id()

    # Store guest with the custom ID (ensure your DB handles this correctly)
    db_guest = create_guest(db, guest)
    db_guest.id = guest_id  # Assign the unique GUEST-<RANDOM_NUMBER> ID

    return db_guest

@router.get("/{guest_id}", response_model=GuestOut)
def read_guest(guest_id: str, db: Session = Depends(get_db)):
    return get_guest(db, guest_id)

@router.get("/", response_model=List[GuestOut])
def read_guests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_guests(db, skip=skip, limit=limit)

@router.put("/{guest_id}", response_model=GuestOut)
def update_existing_guest(guest_id: str, guest_update: GuestUpdate, db: Session = Depends(get_db)):
    return update_guest(db, guest_id, guest_update)

@router.delete("/{guest_id}", response_model=GuestOut)
def delete_existing_guest(guest_id: str, db: Session = Depends(get_db)):
    return delete_guest(db, guest_id)
