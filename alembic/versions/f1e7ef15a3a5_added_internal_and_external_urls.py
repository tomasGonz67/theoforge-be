from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1e7ef15a3a5'
down_revision: Union[str, None] = '2a268f3644a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Instead of dropping the tables, add the new columns to the existing table
    op.add_column('resources', sa.Column('internal_path', sa.String(), nullable=True))
    op.add_column('resources', sa.Column('external_url', sa.String(), nullable=True))


def downgrade() -> None:
    # ✅ Remove the new columns in case we need to rollback
    op.drop_column('resources', 'internal_path')
    op.drop_column('resources', 'external_url')
