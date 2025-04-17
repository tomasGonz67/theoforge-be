
"""
Test configuration and fixtures for the TheoForge Backend.

This module provides pytest fixtures for:
- Database session management
- HTTP client setup
- User fixtures for different test scenarios
"""

from datetime import datetime, timedelta
from uuid import uuid4
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from faker import Faker
from unittest.mock import AsyncMock
from alembic import command
from alembic.config import Config

from app.main import app
from app.database import Base, Database, DbService
from app.models.user import User, UserRole
from app.routers.dependencies import get_db
from app.core.security import hash_password
from app.operations.jwt_service import create_access_token
from settings.config import settings
from app.operations.user import UserRepository, AuthenticationService, RegistrationService
from app.models.guest import Guest, GuestStatus  # ✅ Fixed Import

fake = Faker()

# Same database URL as main app since we're running in Docker
database_url = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/theoforge_dev")
TEST_DATABASE_URL = database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with NullPool to prevent connection reuse
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
    """Initialize the database for testing using Alembic migrations."""
    Database.initialize(database_url)
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")  # ✅ Apply migrations properly
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Ensure test data is cleared without deleting alembic_version."""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != "alembic_version":  # ✅ Skip alembic_version table
                await conn.execute(table.delete())  # ✅ Delete only test data, not schema

    yield  # Run the test

@pytest.fixture(scope="function")
async def db_session():
    """Provide a database session for each test."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="function")
async def async_client(db_session):
    """Provide an async HTTP client for testing API endpoints."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

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
        "email_verified": True
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
        "role": UserRole.USER,
        "email_verified": False
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
        "role": UserRole.USER,
        "email_verified": True
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
        "role": UserRole.USER,
        "email_verified": False
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
            "role": UserRole.USER,
            "email_verified": False
        }
        user = User(**user_data)
        db_session.add(user)
        users.append(user)
    await db_session.commit()
    return users

@pytest.fixture(scope="function")
def admin_token(admin_user):
    token_data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def user_token(user):
    token_data = {"sub": str(user.id), "role": user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def user_repository(db_session):
    """Provide a UserRepository instance for testing."""
    return UserRepository(db_session)

@pytest.fixture(scope="function")
def authentication_service(db_session):
    """Provide an AuthenticationService instance for testing."""
    repository = UserRepository(db_session)
    return AuthenticationService(repository)

@pytest.fixture(scope="function")
def registration_service(db_session):
    """Provide a RegistrationService instance for testing."""
    repository = UserRepository(db_session)
    return RegistrationService(repository)

@pytest.fixture(scope="function")
def db_service():
    """Provide a DbService instance for testing."""
    return DbService

@pytest.fixture(scope="function")
async def test_guest(db_session: AsyncSession):
    """Fixture to create and verify a test guest in the database before running tests."""
    guest_data = {
        "session_id": "test_session_123",
        "page_views": ["/home", "/about"],
        "interaction_events": ["clicked_signup"],
        "status": GuestStatus.NEW,
        "interaction_history": [{"event": "visited_homepage", "timestamp": "2025-03-01T12:00:00Z"}],
    }
    
    guest = Guest(**guest_data)
    db_session.add(guest)
    
    await db_session.commit()
    await db_session.refresh(guest)
    
    stored_guest = await db_session.get(Guest, guest.id)
    assert stored_guest is not None, "Guest was not found in the database after commit!"

    return stored_guest