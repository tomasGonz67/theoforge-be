# app/models/guest.py
from sqlalchemy import Column, String
from app.database.session import Base

class Guest(Base):
    __tablename__ = "guests"

    id = Column(String, primary_key=True, index=True)  # Custom ID like GUEST-1234
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
