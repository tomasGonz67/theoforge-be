"""added knowledge graph fields to resource table

Revision ID: dd0256cacbbf
Revises: 43b0b999030e
Create Date: 2025-03-07 21:00:08.849504

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision: str = 'dd0256cacbbf'
down_revision: Union[str, None] = '43b0b999030e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create the resources table with additional fields
    op.create_table(
        'resources',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('tags', JSONB, nullable=True),  # Store JSON data
        sa.Column('profile_picture', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create the self-referential relationship table for related resources
    op.create_table(
        'resource_association',
        sa.Column('resource_id', UUID(as_uuid=True), sa.ForeignKey('resources.id'), primary_key=True),
        sa.Column('related_resource_id', UUID(as_uuid=True), sa.ForeignKey('resources.id'), primary_key=True),
    )

def downgrade() -> None:
    # Drop the association table first
    op.drop_table('resource_association')
    # Drop the resources table
    op.drop_table('resources')
