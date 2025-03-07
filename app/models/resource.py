import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, TIMESTAMP, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Association table for many-to-many relationship (Self-referential relationships)
resource_association_table = Table(
    "resource_association",
    Base.metadata,
    Column("resource_id", UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
    Column("related_resource_id", UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
)

class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    tags = Column(JSONB, nullable=True)  # Store tags as a JSON list
    profile_picture = Column(String, nullable=True)  # Profile image for the resource
    source_url = Column(String, nullable=True)  # External link to the resource
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)

    # ✅ Fix timestamps for correct PostgreSQL behavior
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=False)

    # ✅ Define relationships
    user = relationship("User", back_populates="resources")

    # ✅ Improved Many-to-Many relationship (Self-referential)
    related_resources = relationship(
        "Resource",
        secondary=resource_association_table,
        primaryjoin=id == resource_association_table.c.resource_id,
        secondaryjoin=id == resource_association_table.c.related_resource_id,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Resource(id={self.id}, name={self.name}, category={self.category}, user_id={self.user_id})>"
