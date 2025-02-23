# app/crud/guest.py
from sqlalchemy.orm import Session
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate
from fastapi import HTTPException
import random

def generate_unique_guest_id():
    return f"GUEST-{random.randint(1000, 9999)}"

def get_guest(db: Session, guest_id: str):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

def get_guests(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Guest).offset(skip).limit(limit).all()

def create_guest(db: Session, guest: GuestCreate):
    # Generate unique guest ID
    guest_id = generate_unique_guest_id()

    db_guest = Guest(
        id=guest_id,  # Assign custom GUEST-XXXX ID
        name=guest.name,
        email=guest.email,
        phone=guest.phone
    )
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest

def update_guest(db: Session, guest_id: str, guest_update: GuestUpdate):
    db_guest = get_guest(db, guest_id)
    for var, value in vars(guest_update).items():
        if value is not None:
            setattr(db_guest, var, value)
    db.commit()
    db.refresh(db_guest)
    return db_guest

def delete_guest(db: Session, guest_id: str):
    db_guest = get_guest(db, guest_id)
    db.delete(db_guest)
    db.commit()
    return db_guest
