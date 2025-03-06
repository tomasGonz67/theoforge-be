"""merge_migration_heads

Revision ID: 43b0b999030e
Revises: 803718c7e04e, effb157da083
Create Date: 2025-03-06 19:02:00.163721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43b0b999030e'
down_revision: Union[str, None] = ('803718c7e04e', 'effb157da083')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
