import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole, SubscriptionPlan
from app.core.security import hash_password
import uuid
from datetime import datetime

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user with required fields."""
    user_data = {
        "email": "test@example.com",
        "nickname": "test_user",
        "hashed_password": hash_password("SecurePass123!"),
        "role": UserRole.USER,
        "email_verified": False
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.email == user_data["email"]
    assert user.nickname == user_data["nickname"]
    assert user.role == UserRole.USER
    assert not user.email_verified
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None

@pytest.mark.asyncio
async def test_create_first_user_as_admin(db_session: AsyncSession):
    """Test that the first user gets admin role."""
    first_user = User(
        email="admin@example.com",
        nickname="admin",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.ADMIN,
        email_verified=True
    )
    db_session.add(first_user)
    await db_session.commit()
    
    second_user = User(
        email="user@example.com",
        nickname="user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER,
        email_verified=False
    )
    db_session.add(second_user)
    await db_session.commit()
    
    assert first_user.role == UserRole.ADMIN
    assert second_user.role == UserRole.USER

@pytest.mark.asyncio
async def test_user_role_check(db_session: AsyncSession):
    """Test the has_role method."""
    user = User(
        email="test@example.com",
        nickname="test_user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.commit()

    assert user.has_role(UserRole.USER)
    assert not user.has_role(UserRole.ADMIN)

@pytest.mark.asyncio
async def test_user_email_verification(db_session: AsyncSession):
    """Test email verification functionality."""
    user = User(
        email="test@example.com",
        nickname="test_user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER,
        email_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    
    assert not user.email_verified
    
    user.verify_email()
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.email_verified

@pytest.mark.asyncio
async def test_user_representation(db_session: AsyncSession):
    """Test the string representation of the User model."""
    user = User(
        email="test@example.com",
        nickname="test_user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER,
        subscription_plan=SubscriptionPlan.FREE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    expected_repr = f"<User {user.nickname}, Role: {user.role.name}, Subscription: {user.subscription_plan.name}>"
    assert str(user) == expected_repr
    assert repr(user) == expected_repr

@pytest.mark.asyncio
async def test_optional_fields(db_session: AsyncSession):
    """Test that optional fields can be null."""
    user = User(
        email="test@example.com",
        nickname="test_user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.commit()
    
    assert user.first_name is None
    assert user.last_name is None
    assert user.verification_token is None