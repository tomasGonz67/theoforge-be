"""
Integration tests for the DbService class.

These tests verify that the DbService correctly interacts with the database:
- Transaction isolation
- Concurrent operations
- Error handling with real database
"""
import pytest
import asyncio
from sqlalchemy import text, select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import DbService
from app.models.user import User, UserRole
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_db_service_transaction_isolation(db_session: AsyncSession):
    """Test that transactions are properly isolated."""
    # Arrange
    test_email = "transaction_test@example.com"
    test_nickname = "transaction_test"
    
    # Create a user but don't commit
    insert_stmt = insert(User).values(
        email=test_email,
        nickname=test_nickname,
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    await DbService.execute_query(db_session, insert_stmt, commit=False)
    
    # Now in a separate session, try to find the user
    async with AsyncSession(db_session.bind) as new_session:
        select_stmt = select(User).where(User.email == test_email)
        result = await DbService.execute_query(new_session, select_stmt)
        user_before_commit = result.scalars().first()
    
    # Act
    # Now commit in the original session
    await DbService.commit(db_session)
    
    # And try to find the user again in another session
    async with AsyncSession(db_session.bind) as final_session:
        select_stmt = select(User).where(User.email == test_email)
        result = await DbService.execute_query(final_session, select_stmt)
        user_after_commit = result.scalars().first()
    
    # Assert
    assert user_before_commit is None  # Should not be visible before commit
    assert user_after_commit is not None  # Should be visible after commit
    assert user_after_commit.email == test_email

@pytest.mark.asyncio
async def test_db_service_error_handling(db_session: AsyncSession):
    """Test that database errors are properly handled and don't corrupt session."""
    # Arrange
    test_email = "error_test@example.com"
    test_nickname = "error_test"
    
    # First try an invalid query
    try:
        await DbService.execute_query(db_session, text("SELECT * FROM nonexistent_table"))
    except SQLAlchemyError:
        # Expected error, ignore it
        pass
    
    # Now try a valid query to ensure session is still usable
    insert_stmt = insert(User).values(
        email=test_email,
        nickname=test_nickname,
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    
    # Act
    await DbService.execute_query(db_session, insert_stmt, commit=True)
    
    # Assert - if we got here without errors, the session is still usable
    select_stmt = select(User).where(User.email == test_email)
    result = await DbService.execute_query(db_session, select_stmt)
    user = result.scalars().first()
    
    assert user is not None
    assert user.email == test_email

@pytest.mark.asyncio
async def test_db_service_concurrent_operations(db_session: AsyncSession):
    """Test that concurrent database operations work correctly."""
    # This test simulates multiple concurrent operations
    
    async def create_user(index):
        """Helper function to create a user with unique email."""
        email = f"concurrent{index}@example.com"
        nickname = f"concurrent{index}"
        
        # Create a new session for each operation
        async with AsyncSession(db_session.bind) as session:
            insert_stmt = insert(User).values(
                email=email,
                nickname=nickname,
                hashed_password=hash_password("SecurePass123!"),
                role=UserRole.USER
            )
            await DbService.execute_query(session, insert_stmt, commit=True)
            return email
    
    # Create 5 users concurrently
    emails = await asyncio.gather(*[create_user(i) for i in range(5)])
    
    # Verify all users were created
    created_users = 0
    for email in emails:
        select_stmt = select(User).where(User.email == email)
        result = await DbService.execute_query(db_session, select_stmt)
        user = result.scalars().first()
        if user is not None:
            created_users += 1
    
    assert created_users == 5  # All 5 users should be created 