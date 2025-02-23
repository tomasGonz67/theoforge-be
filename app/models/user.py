from builtins import bool, int, str
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, func, Enum as SQLAlchemyEnum
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class UserRole(Enum):
    """Enumeration of user roles within the application, stored as ENUM in the database."""
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    """
    Represents a user within the application, corresponding to the 'users' table in the database.
    This class uses SQLAlchemy ORM for mapping attributes to database columns efficiently.
    
    Attributes:
        id (UUID): Unique identifier for the user.
        nickname (str): Unique nickname for privacy, required.
        email (str): Unique email address, required.
        email_verified (bool): Flag indicating if the email has been verified.
        hashed_password (str): Hashed password for security, required.
        first_name (str): Optional first name of the user.
        last_name (str): Optional first name of the user.

        bio (str): Optional biographical information.
        profile_picture_url (str): Optional URL to a profile picture.
        linkedin_profile_url (str): Optional LinkedIn profile URL.
        github_profile_url (str): Optional GitHub profile URL.
        role (UserRole): Role of the user within the application.
        is_professional (bool): Flag indicating professional status.
        professional_status_updated_at (datetime): Timestamp of last professional status update.
        last_login_at (datetime): Timestamp of the last login.
        failed_login_attempts (int): Count of failed login attempts.
        is_locked (bool): Flag indicating if the account is locked.
        created_at (datetime): Timestamp when the user was created, set by the server.
        updated_at (datetime): Timestamp of the last update, set by the server.

    Methods:
        lock_account(): Locks the user account.
        unlock_account(): Unlocks the user account.
        verify_email(): Marks the user's email as verified.
        has_role(role_name): Checks if the user has a specified role.
        update_professional_status(status): Updates the professional status and logs the update time.
    """
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    first_name: Mapped[str] = Column(String(100), nullable=True)
    last_name: Mapped[str] = Column(String(100), nullable=True)
    role: Mapped[UserRole] = Column(SQLAlchemyEnum(UserRole, name='UserRole', create_constraint=True), nullable=False)
    email_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        """Provides a readable representation of a user object."""
        return f"<User {self.nickname}, Role: {self.role.name}>"

    def verify_email(self):
        """Marks the user's email as verified."""
        self.email_verified = True

    def has_role(self, role_name: UserRole) -> bool:
        """Checks if the user has a specified role."""
        return self.role == role_name

"""
Changes made for registration implementation:
1. Simplified UserRole to only USER and ADMIN
2. Kept only registration-essential fields:
   - Basic user fields (id, email, hashed_password, nickname, names, role)
   - Email verification fields (email_verified, verification_token)
   - Timestamps (created_at, updated_at)
3. Removed non-registration fields:
   - Profile fields (bio, profile_picture_url, linkedin/github URLs)
   - Professional status fields (is_professional, status update time)
   - Login-specific fields (login attempts, lock status, last login)
4. Role and verification handling:
   - First user gets ADMIN role with email_verified=True
   - Subsequent users get USER role with email_verified=False
   - Email verification can be set via verify_email() method
5. Kept only relevant methods (verify_email, has_role) 
"""
