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

# Define Enum for guest engagement status
class GuestEngagementStatus(str, Enum):
    NEW_VISITOR = "NEW_VISITOR"
    ENGAGED = "ENGAGED"
    RETURNING = "RETURNING"

class Guest(Base):
    __tablename__ = "guests"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Remove PII fields like name, company, contact info
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=False)  # Stores a hashed or anonymous session ID
    page_views: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)  # Tracks visited pages
    interaction_events: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)  # Tracks actions like clicks, form interactions

    engagement_status: Mapped[GuestEngagementStatus] = mapped_column(SQLAlchemyEnum(GuestEngagementStatus), default=GuestEngagementStatus.NEW_VISITOR, nullable=False)

    first_visit_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Track behavior in a privacy-conscious way
    interaction_history: Mapped[Optional[List[Dict]]] = mapped_column(
        MutableList.as_mutable(JSONB), nullable=True, default=list
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Guest Session {self.session_id[:8]}, Status: {self.engagement_status.value}>"

# Event listener to update last_interaction when interaction_history changes
@event.listens_for(Guest.interaction_history, "set", propagate=True)
def update_last_interaction(target, value, oldvalue, initiator):
    if value != oldvalue:  # Check if the history was modified
        target.last_interaction = datetime.utcnow()
