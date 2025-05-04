"""Fix user-resource relationship"""

from alembic import op
import sqlalchemy as sa

# ✅ Add these lines if they are missing
revision = "774014b9c8ba"  # Unique ID of this migration
down_revision = "32ea415e5c3c"  # ID of the previous migration
branch_labels = None
depends_on = None

def upgrade():
    op.drop_table("resource_association")  # Drop association table first
    op.drop_table("resources")  # Now drop `resources` table

    # Recreate `resources` table with correct relationships
    op.create_table(
        "resources",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("profile_picture", sa.String, nullable=True),
        sa.Column("source_url", sa.String, nullable=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_public", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # ✅ Recreate `resource_association` table after recreating `resources`
    op.create_table(
        "resource_association",
        sa.Column("resource_id", sa.UUID, sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("related_resource_id", sa.UUID, sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
    )

def downgrade():
    op.drop_table("resource_association")
    op.drop_table("resources")
