from datetime import datetime
import uuid
from typing import Optional, List, Dict
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

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

    first_contact_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation_history: Mapped[Optional[List[Dict]]] = mapped_column(JSONB, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Guest {self.name or 'Unknown'}, Company: {self.company or 'N/A'}>"
