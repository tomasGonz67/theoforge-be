"""fix resource model relationships

Revision ID: 2f1be34c83ba
Revises: 774014b9c8ba
Create Date: 2025-03-07 23:15:03.918053

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "2f1be34c83ba"
down_revision: Union[str, None] = "774014b9c8ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Drop constraints from `resource_association` before dropping tables
    op.drop_constraint("resource_association_resource_id_fkey", "resource_association", type_="foreignkey")
    op.drop_constraint("resource_association_related_resource_id_fkey", "resource_association", type_="foreignkey")

    # ✅ Drop the `resource_association` table first
    op.drop_table("resource_association")

    # ✅ Now drop the `resources` table
    op.drop_table("resources")

    # ✅ Recreate the `resources` table with correct constraints
    op.create_table(
        "resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("tags", JSONB, nullable=True),
        sa.Column("profile_picture", sa.String, nullable=True),
        sa.Column("source_url", sa.String, nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_public", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # ✅ Recreate `resource_association` table with CASCADE foreign keys
    op.create_table(
        "resource_association",
        sa.Column("resource_id", UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("related_resource_id", UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    # Reverse the operations for rollback
    op.drop_table("resource_association")
    op.drop_table("resources")

    # ✅ Restore `resources`
    op.create_table(
        "resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("tags", JSONB, nullable=True),
        sa.Column("profile_picture", sa.String, nullable=True),
        sa.Column("source_url", sa.String, nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_public", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # ✅ Restore `resource_association`
    op.create_table(
        "resource_association",
        sa.Column("resource_id", UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("related_resource_id", UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
    )
