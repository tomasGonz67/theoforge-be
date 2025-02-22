from sqlalchemy.orm import Session
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate
from fastapi import HTTPException

def get_guest(db: Session, guest_id: int):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

def get_guests(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Guest).offset(skip).limit(limit).all()

def create_guest(db: Session, guest: GuestCreate):
    # Pre-checks for unique name and email
    existing_username = db.query(Guest).filter(Guest.name == guest.name).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists.")

    existing_email = db.query(Guest).filter(Guest.email == guest.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists.")

    db_guest = Guest(**guest.dict())
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest

def update_guest(db: Session, guest_id: int, guest_update: GuestUpdate):
    db_guest = get_guest(db, guest_id)
    for var, value in vars(guest_update).items():
        if value is not None:
            setattr(db_guest, var, value)
    db.commit()
    db.refresh(db_guest)
    return db_guest

def delete_guest(db: Session, guest_id: int):
    db_guest = get_guest(db, guest_id)
    db.delete(db_guest)
    db.commit()
    return db_guest
