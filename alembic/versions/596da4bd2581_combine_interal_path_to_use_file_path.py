"""combine internal_path to use file_path

Revision ID: 596da4bd2581
Revises: f1e7ef15a3a5
Create Date: 2025-03-11 12:33:30.932856

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '596da4bd2581'
down_revision: Union[str, None] = 'f1e7ef15a3a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ✅ Drop `internal_path` column instead of dropping the entire `resources` table
    op.drop_column('resources', 'internal_path')

def downgrade() -> None:
    # ✅ If rolling back, add `internal_path` back
    op.add_column('resources', sa.Column('internal_path', sa.VARCHAR(), nullable=True))
