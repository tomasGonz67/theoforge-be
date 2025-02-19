# User model definition
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, func, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base 

class UserRole(Enum):
    """Basic user roles"""
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[UserRole] = Column(SQLAlchemyEnum(UserRole, name='user_role'), nullable=False, default=UserRole.USER)
    email_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = Column(Integer, default=0)
    is_locked: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verification_token = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def lock_account(self):
        self.is_locked = True

    def unlock_account(self):
        self.is_locked = False

    def verify_email(self):
        self.email_verified = True

    def has_role(self, role_name: UserRole) -> bool:
        return self.role == role_name

"""
Not included from user_management:
nickname
first_name
last_name
bio
profile_picture_url
linkedin_profile_url
github_profile_url
is_professional
professional_status_updated_at
last_login_at

Removed from UserRole Enum:
ANONYMOUS
AUTHENTICATED
MANAGER (Kept only USER and ADMIN)

Removed Methods:
update_professional_status()
"""