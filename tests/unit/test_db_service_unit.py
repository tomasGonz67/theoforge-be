"""
Unit tests for the DbService class.

These tests verify that the DbService correctly handles:
- Query execution
- Transaction management (commit/rollback)
- Error handling
"""
import pytest
from sqlalchemy import text, select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import DbService
from app.models.user import User, UserRole

@pytest.mark.asyncio
async def test_execute_query_select(db_session: AsyncSession):
    """Test that execute_query can run a simple SELECT query."""
    # Arrange
    test_query = text("SELECT 1 as test_value")
    
    # Act
    result = await DbService.execute_query(db_session, test_query)
    row = result.fetchone()
    
    # Assert
    assert row is not None
    assert row[0] == 1

@pytest.mark.asyncio
async def test_execute_query_with_params(db_session: AsyncSession):
    """Test that execute_query can run a query with parameters."""
    # Arrange
    test_value = 42
    test_query = text("SELECT :value as test_value").bindparams(value=test_value)
    
    # Act
    result = await DbService.execute_query(
        db_session, 
        test_query
    )
    row = result.fetchone()
    
    # Assert
    assert row is not None
    assert row[0] == test_value

@pytest.mark.asyncio
async def test_execute_query_insert(db_session: AsyncSession, user):
    """Test that execute_query can perform an insert operation."""
    # Arrange
    new_email = "newuser@example.com"
    new_nickname = "newuser"
    
    insert_stmt = insert(User).values(
        email=new_email,
        nickname=new_nickname,
        hashed_password=user.hashed_password,  # Reuse from fixture for simplicity
        role=UserRole.USER,  # Adding the required role field
        email_verified=False
    )
    
    # Act
    await DbService.execute_query(db_session, insert_stmt, commit=True)
    
    # Query to verify the insert worked
    select_stmt = select(User).where(User.email == new_email)
    result = await DbService.execute_query(db_session, select_stmt)
    inserted_user = result.scalars().first()
    
    # Assert
    assert inserted_user is not None
    assert inserted_user.email == new_email
    assert inserted_user.nickname == new_nickname

@pytest.mark.asyncio
async def test_commit(db_session: AsyncSession):
    """Test that commit properly persists changes."""
    # Arrange
    new_email = "commituser@example.com"
    new_nickname = "commituser"
    
    # Add a user but don't commit yet
    insert_stmt = insert(User).values(
        email=new_email,
        nickname=new_nickname,
        hashed_password="dummyhash",
        role=UserRole.USER,  # Adding the required role field
        email_verified=False
    )
    await DbService.execute_query(db_session, insert_stmt, commit=False)
    
    # Act
    await DbService.commit(db_session)
    
    # Query in a new session to verify commit worked
    async with AsyncSession(db_session.bind) as new_session:
        select_stmt = select(User).where(User.email == new_email)
        result = await DbService.execute_query(new_session, select_stmt)
        committed_user = result.scalars().first()
    
    # Assert
    assert committed_user is not None
    assert committed_user.email == new_email

@pytest.mark.asyncio
async def test_rollback(db_session: AsyncSession):
    """Test that rollback properly discards changes."""
    # Arrange
    new_email = "rollbackuser@example.com"
    new_nickname = "rollbackuser"
    
    # Add a user but don't commit
    insert_stmt = insert(User).values(
        email=new_email,
        nickname=new_nickname,
        hashed_password="dummyhash",
        role=UserRole.USER,  # Adding the required role field
        email_verified=False
    )
    await DbService.execute_query(db_session, insert_stmt, commit=False)
    
    # Act
    await DbService.rollback(db_session)
    
    # Query to verify the rollback worked
    select_stmt = select(User).where(User.email == new_email)
    result = await DbService.execute_query(db_session, select_stmt)
    rolled_back_user = result.scalars().first()
    
    # Assert
    assert rolled_back_user is None  # User should not exist after rollback

@pytest.mark.asyncio
async def test_error_handling(db_session: AsyncSession):
    """Test that SQLAlchemy errors are handled properly."""
    # Arrange
    # Create an invalid query
    invalid_query = text("SELECT * FROM nonexistent_table")
    
    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await DbService.execute_query(db_session, invalid_query) 