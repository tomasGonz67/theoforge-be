from sqlalchemy import Column, String, ForeignKey, Boolean, TIMESTAMP, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import uuid
from app.database import Base

# Association table for many-to-many related resources
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
    tags = Column(JSONB, nullable=True)  # JSON column
    profile_picture = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # ✅ Corrected User Relationship (One-to-Many)
    user = relationship("User", back_populates="resources", lazy="joined")

    # ✅ Fixed Many-to-Many Relationship for related resources
    related_resources = relationship(
        "Resource",
        secondary=resource_association_table,
        primaryjoin=id == resource_association_table.c.resource_id,
        secondaryjoin=id == resource_association_table.c.related_resource_id,
        backref=backref("related_to", lazy="selectin"),  # ✅ Fixes async issue
        lazy="selectin",  # ✅ Fixes MissingGreenlet issue
    )

    def __repr__(self):
        return f"<Resource(id={self.id}, name={self.name}, user_id={self.user_id})>"
