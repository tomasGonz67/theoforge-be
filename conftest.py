"""
File: conftest.py

Overview:
This Python test file utilizes pytest to manage database states and HTTP clients for testing a web application built with FastAPI and SQLAlchemy. It includes detailed fixtures to mock the testing environment, ensuring each test is run in isolation with a consistent setup.
"""

# Standard library imports
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
import uuid

# Third-party imports
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session
from faker import Faker

# Application-specific imports
from app.main import app
from app.database import Base, Database
from app.models.user import User, UserRole
from app.dependencies import get_db, get_settings
from app.utils.security import hash_password
from app.services.auth import create_access_token

fake = Faker()

settings = get_settings()
# Use a separate test database URL
TEST_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
if not TEST_DATABASE_URL.endswith("_test"):
    TEST_DATABASE_URL += "_test"

engine = create_async_engine(TEST_DATABASE_URL)  # Removed debug flag
AsyncTestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
AsyncSessionScoped = scoped_session(AsyncTestingSessionLocal)

@pytest.fixture(scope="function")
async def async_client(db_session):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    try:
        Database.initialize(TEST_DATABASE_URL)
    except Exception as e:
        pytest.fail(f"Failed to initialize the database: {str(e)}")

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(setup_database):
    async with AsyncSessionScoped() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="function")
async def locked_user(db_session):
    user_data = {
        "email": fake.email(),
        "hashed_password": hash_password("TestPassword123!"),
        "role": UserRole.USER,
        "email_verified": False,
        "is_locked": True,
        "failed_login_attempts": settings.max_login_attempts,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def regular_user(db_session):
    user_data = {
        "email": fake.email(),
        "hashed_password": hash_password("TestPassword123!"),
        "role": UserRole.USER,
        "email_verified": False,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def verified_user(db_session):
    user_data = {
        "email": fake.email(),
        "hashed_password": hash_password("TestPassword123!"),
        "role": UserRole.USER,
        "email_verified": True,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def admin_user(db_session):
    user_data = {
        "email": "admin@example.com",
        "hashed_password": hash_password("AdminPass123!"),
        "role": UserRole.ADMIN,
        "email_verified": True,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def multiple_users(db_session):
    users = []
    for _ in range(50):
        user_data = {
            "email": fake.email(),
            "hashed_password": hash_password("TestPassword123!"),
            "role": UserRole.USER,
            "email_verified": False,
            "is_locked": False,
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
def user_token(regular_user):
    token_data = {"sub": str(regular_user.id), "role": regular_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30)) 