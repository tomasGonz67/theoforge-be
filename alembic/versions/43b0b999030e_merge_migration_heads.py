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
    # Re-add the missing columns to ensure they exist
    # Define the ENUM type
    subscription_plan_enum = sa.Enum('FREE', 'BASIC', 'PREMIUM', name='SubscriptionPlan', create_constraint=True)
    
    # Create the ENUM type in the database if it doesn't exist
    subscription_plan_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns safely by checking if they exist first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    # Add login-related columns from effb157da083
    if 'failed_login_attempts' not in columns:
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    if 'is_locked' not in columns:
        op.add_column('users', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add profile-related columns from 803718c7e04e
    if 'phone_number' not in columns:
        op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    if 'address' not in columns:
        op.add_column('users', sa.Column('address', sa.String(length=255), nullable=True))
    if 'city' not in columns:
        op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    if 'state' not in columns:
        op.add_column('users', sa.Column('state', sa.String(length=50), nullable=True))
    if 'zip_code' not in columns:
        op.add_column('users', sa.Column('zip_code', sa.String(length=20), nullable=True))
    if 'card_number' not in columns:
        op.add_column('users', sa.Column('card_number', sa.String(length=16), nullable=True))
    if 'ccv' not in columns:
        op.add_column('users', sa.Column('ccv', sa.String(length=4), nullable=True))
    if 'security_code' not in columns:
        op.add_column('users', sa.Column('security_code', sa.String(length=4), nullable=True))
    if 'subscription_plan' not in columns:
        op.add_column('users', sa.Column('subscription_plan', subscription_plan_enum, nullable=False, server_default='FREE'))
    
    # Check if unique constraint exists before adding it
    # Note: This is a simplified check, might need to be adjusted
    try:
        op.create_unique_constraint(None, 'users', ['phone_number'])
    except Exception:
        # Constraint might already exist, which is fine
        pass


def downgrade() -> None:
    pass
