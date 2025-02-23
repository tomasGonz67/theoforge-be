# app/crud/user.py

from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException
import random
from faker import Faker

# Initialize Faker
fake = Faker()

def generate_unique_user_id():
    return f"USER-{random.randint(1000, 9999)}"

def generate_random_username():
    return fake.user_name()

def get_user(db: Session, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    # Generate unique user ID
    user_id = generate_unique_user_id()

    # Auto-generate random username if not provided
    username = user.username.strip() if user.username.strip() else generate_random_username()

    # Check for existing username or email
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists. Try again.")

    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists.")

    db_user = User(
        id=user_id,
        username=username,
        email=user.email,
        full_name=user.full_name
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_update: UserUpdate):
    db_user = get_user(db, user_id)
    for var, value in vars(user_update).items():
        if value is not None:
            setattr(db_user, var, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str):
    db_user = get_user(db, user_id)
    db.delete(db_user)
    db.commit()
    return db_user
