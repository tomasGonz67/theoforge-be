from datetime import datetime
import uuid
from typing import Optional, List, Dict
from enum import Enum
from sqlalchemy import String, DateTime, func, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import event
from app.database import Base

# Define Enum for guest status
class GuestStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    CONVERTED = "CONVERTED"

class Guest(Base):
    __tablename__ = "guests"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    project_type: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    budget: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timeline: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pain_points: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    current_tech: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    additional_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[GuestStatus] = mapped_column(SQLAlchemyEnum(GuestStatus), default=GuestStatus.NEW, nullable=False)

    first_contact_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Use MutableList for tracking JSONB changes
    conversation_history: Mapped[Optional[List[Dict]]] = mapped_column(
        MutableList.as_mutable(JSONB), nullable=True, default=list
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Guest {self.name or 'Unknown'}, Company: {self.company or 'N/A'}, Status: {self.status.value}>"

# Event listener to update last_interaction when conversation_history changes
@event.listens_for(Guest.conversation_history, "set", propagate=True)
def update_last_interaction(target, value, oldvalue, initiator):
    if value != oldvalue:  # Check if the history was modified
        target.last_interaction = datetime.utcnow()