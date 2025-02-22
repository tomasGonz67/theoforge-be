from sqlalchemy import Column, Integer, String
from app.database.session import Base

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # <-- Enforce unique constraint
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
