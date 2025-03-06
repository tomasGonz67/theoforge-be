"""add user profile datasets

Revision ID: 803718c7e04e
Revises: 8a100fbfdb31
Create Date: 2025-03-05 16:45:17.542424

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '803718c7e04e'
down_revision: Union[str, None] = '8a100fbfdb31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the ENUM type before using it
subscription_plan_enum = sa.Enum('FREE', 'BASIC', 'PREMIUM', name='SubscriptionPlan', create_constraint=True)

def upgrade() -> None:
    # Create the ENUM type in the database first
    subscription_plan_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to the users table
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('address', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('zip_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('card_number', sa.String(length=16), nullable=True))
    op.add_column('users', sa.Column('ccv', sa.String(length=4), nullable=True))
    op.add_column('users', sa.Column('security_code', sa.String(length=4), nullable=True))
    op.add_column('users', sa.Column('subscription_plan', subscription_plan_enum, nullable=False, server_default='FREE'))
    
    # Add unique constraint on phone_number
    op.create_unique_constraint(None, 'users', ['phone_number'])

def downgrade() -> None:
    # Remove columns from the users table
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'subscription_plan')
    op.drop_column('users', 'security_code')
    op.drop_column('users', 'ccv')
    op.drop_column('users', 'card_number')
    op.drop_column('users', 'zip_code')
    op.drop_column('users', 'state')
    op.drop_column('users', 'city')
    op.drop_column('users', 'address')
    op.drop_column('users', 'phone_number')

    # Drop ENUM type
    subscription_plan_enum.drop(op.get_bind(), checkfirst=True)
