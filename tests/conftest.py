"""
Test configuration and fixtures for the TheoForge Backend.

This module provides pytest fixtures for:
- Database session management
- HTTP client setup
- User fixtures for different test scenarios
"""

from datetime import datetime
from uuid import uuid4
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from faker import Faker

from app.main import app
from app.database import Base, Database
from app.models.user import User, UserRole
from app.auth.dependencies import get_db
from app.core.security import hash_password

fake = Faker()

# same database URL as main app since we're running in Docker
database_url = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/theoforge_dev")
TEST_DATABASE_URL = database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create engine with NullPool to prevent connection reuse
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=True
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session", autouse=True)
async def initialize_database():
    """Initialize the database for testing."""
    Database.initialize(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def async_client(db_session):
    """Provide an async HTTP client for testing API endpoints."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Set up a clean database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(setup_database):
    """Provide a database session for each test."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="function")
async def user(db_session):
    """Create a regular user for testing."""
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("SecurePass123!"),
        "role": UserRole.USER,
        "email_verified": False
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def admin_user(db_session):
    """Create an admin user for testing."""
    user_data = {
        "nickname": "admin_user",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "hashed_password": hash_password("SecurePass123!"),
        "role": UserRole.ADMIN,
        "email_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def locked_user(db_session):
    unique_email = fake.email()
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": unique_email,
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": True,
        "failed_login_attempts": settings.max_login_attempts,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def verified_user(db_session):
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": True,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def unverified_user(db_session):
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def users_with_same_role_50_users(db_session):
    users = []
    for _ in range(50):
        user_data = {
            "nickname": fake.user_name(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "hashed_password": fake.password(),
            "role": UserRole.AUTHENTICATED,
            "email_verified": False,
            "is_locked": False,
        }
        user = User(**user_data)
        db_session.add(user)
        users.append(user)
    await db_session.commit()
    return users

# Configure a fixture for each type of user role you want to test
@pytest.fixture(scope="function")
def admin_token(admin_user):
    # Assuming admin_user has an 'id' and 'role' attribute
    token_data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def user_token(user):
    token_data = {"sub": str(user.id), "role": user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture
def email_service():
    if settings.send_real_mail == 'true':
        # Return the real email service when specifically testing email functionality
        return EmailService()
    else:
        # Otherwise, use a mock to prevent actual email sending
        mock_service = AsyncMock(spec=EmailService)
        mock_service.send_verification_email.return_value = None
        mock_service.send_user_email.return_value = None
        return mock_service


