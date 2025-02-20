"""
File: conftest.py

Overview:
This Python test file utilizes pytest to manage database states and HTTP clients for testing a web application built with FastAPI and SQLAlchemy. It includes detailed fixtures to mock the testing environment, ensuring each test is run in isolation with a consistent setup.
"""

# Standard library imports
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
import uuid
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from faker import Faker
from sqlalchemy import text

# Application-specific imports
from app.main import app
from app.database import Base, Database
from app.models.user import User, UserRole
from app.dependencies import get_db, get_settings
from app.utils.security import hash_password
from app.services.auth import create_access_token

fake = Faker()

settings = get_settings()
# First connect to default postgres database to create test database
POSTGRES_DATABASE_URL = 'postgresql+asyncpg://postgres:postgres123@localhost/postgres'
TEST_DATABASE_URL = 'postgresql+asyncpg://postgres:postgres123@localhost/theoforge_test'

postgres_engine = create_async_engine(
    POSTGRES_DATABASE_URL,
    isolation_level="AUTOCOMMIT"
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    isolation_level="AUTOCOMMIT"
)

AsyncTestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_db():
    """Create test database."""
    async with postgres_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS theoforge_test"))
        await conn.execute(text("CREATE DATABASE theoforge_test"))
    await postgres_engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def setup_database(create_test_db):
    """Set up the database for testing."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncSession:
    """Create a fresh database session for a test."""
    async with AsyncTestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session):
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create a regular test user."""
    user = User(
        email=fake.email(),
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def locked_user(db_session: AsyncSession) -> User:
    """Create a locked test user."""
    user = User(
        email=fake.email(),
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        is_locked=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def verified_user(db_session: AsyncSession) -> User:
    """Create a verified test user."""
    user = User(
        email=fake.email(),
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email=fake.email(),
        hashed_password=hash_password("testpassword123"),
        role=UserRole.ADMIN,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def multiple_users(db_session: AsyncSession) -> list[User]:
    """Create multiple test users."""
    users = []
    for _ in range(3):
        user = User(
            email=fake.email(),
            hashed_password=hash_password("testpassword123"),
            role=UserRole.USER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        users.append(user)
    
    for user in users:
        db_session.add(user)
    await db_session.commit()
    
    for user in users:
        await db_session.refresh(user)
    
    return users

@pytest.fixture(scope="function")
async def admin_token(admin_user):
    """Create an admin token."""
    token_data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
async def user_token(regular_user):
    """Create a user token."""
    token_data = {"sub": str(regular_user.id), "role": regular_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30)) 