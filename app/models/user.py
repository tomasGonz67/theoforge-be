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

class SubscriptionPlan(Enum):
    """Enumeration of available subscription plans."""
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"

class User(Base):
    """
    Represents a user within the application, corresponding to the 'users' table in the database.
    This class uses SQLAlchemy ORM for mapping attributes to database columns efficiently.
    """
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = Column(String(50), unique=True, nullable=True, index=True)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    first_name: Mapped[str] = Column(String(100), nullable=True)
    last_name: Mapped[str] = Column(String(100), nullable=True)
    role: Mapped[UserRole] = Column(SQLAlchemyEnum(UserRole, name='UserRole', create_constraint=True), nullable=False)
    email_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Contact Information
    phone_number: Mapped[str] = Column(String(20), unique=True, nullable=True)
    
    # Address Information
    address: Mapped[str] = Column(String(255), nullable=True)
    city: Mapped[str] = Column(String(100), nullable=True)
    state: Mapped[str] = Column(String(50), nullable=True)
    zip_code: Mapped[str] = Column(String(20), nullable=True)
    
    # Payment Information
    card_number: Mapped[str] = Column(String(16), nullable=True)
    ccv: Mapped[str] = Column(String(4), nullable=True)
    security_code: Mapped[str] = Column(String(4), nullable=True)
    
    # Subscription Plan
    subscription_plan: Mapped[SubscriptionPlan] = Column(SQLAlchemyEnum(SubscriptionPlan, name='SubscriptionPlan', create_constraint=True), nullable=False, default=SubscriptionPlan.FREE)
    
    def __repr__(self) -> str:
        """Provides a readable representation of a user object."""
        return f"<User {self.nickname}, Role: {self.role.name}, Subscription: {self.subscription_plan.name}>"

    def verify_email(self):
        """Marks the user's email as verified."""
        self.email_verified = True

    def has_role(self, role_name: UserRole) -> bool:
        """Checks if the user has a specified role."""
        return self.role == role_name
