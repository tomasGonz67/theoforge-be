from sqlalchemy import Column, Integer, String
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)  # Unique username
    email = Column(String, unique=True, index=True, nullable=False)     # Unique email
    full_name = Column(String, nullable=True)
