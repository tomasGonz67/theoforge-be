# app/routers/user.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from faker import Faker

from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.crud.user import get_user, get_users, create_user, update_user, delete_user
from app.database.session import SessionLocal

router = APIRouter(prefix="/users", tags=["Users"])

# Initialize Faker
fake = Faker()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=UserOut)
def create_new_user(
    user: UserCreate = Body(
        ...,
        example={
            "username": fake.user_name(),
            "email": fake.email(),
            "full_name": fake.name()
        }
    ),
    db: Session = Depends(get_db)
):
    return create_user(db, user)

@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=List[UserOut])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)

@router.put("/{user_id}", response_model=UserOut)
def update_existing_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=UserOut)
def delete_existing_user(user_id: str, db: Session = Depends(get_db)):
    db_user = delete_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
