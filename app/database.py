from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from threading import Lock
from builtins import ValueError, bool
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

Base = declarative_base()
logger = logging.getLogger(__name__)

class Database:
    """Handles database connections and sessions."""
    _engine = None
    _session_factory = None
    _lock = Lock()  

    @classmethod
    def initialize(cls, database_url: str, echo: bool = False):
        """Initialize the async engine and sessionmaker. Thread-safe initialization."""
        with cls._lock:  
            if cls._engine is None:
                cls._engine = create_async_engine(
                    database_url, 
                    echo=echo, 
                    future=True,
                    poolclass=NullPool  # Use NullPool to prevent connection reuse
                )
                cls._session_factory = sessionmaker(
                    bind=cls._engine, 
                    class_=AsyncSession, 
                    expire_on_commit=False, 
                    future=True
                )

    @classmethod
    def get_session_factory(cls):
        """Returns the session factory, ensuring it's initialized."""
        with cls._lock:  # thread-safe access
            if cls._session_factory is None:
                raise ValueError("Database not initialized. Call `initialize()` first.")
            return cls._session_factory

    @classmethod
    def dispose_engine(cls):
        """Dispose of the engine explicitly when done, for clean-up."""
        with cls._lock:
            if cls._engine is not None:
                cls._engine.sync_engine.dispose()
                cls._engine = None
                cls._session_factory = None

class DbService:
    """
    Provides centralized database query execution services.
    This abstraction handles query execution, error handling, and transaction management.
    """
    
    @classmethod
    async def execute_query(cls, session: AsyncSession, query, commit=False):
        """
        Execute a database query with proper error handling and transaction management.
        
        Args:
            session: The database session
            query: The query to execute
            commit: Whether to commit the transaction after execution
            
        Returns:
            The result of the query execution
            
        Raises:
            SQLAlchemyError: If a database error occurs
        """
        try:
            logger.debug(f"Executing query: {query}")
            result = await session.execute(query)
            if commit:
                logger.debug("Committing transaction")
                await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            # Always roll back on error, regardless of commit parameter
            logger.debug("Rolling back transaction")
            await session.rollback()
            raise

    @classmethod
    async def commit(cls, session: AsyncSession):
        """
        Commit a transaction.
        
        Args:
            session: The database session
            
        Raises:
            SQLAlchemyError: If a database error occurs
        """
        try:
            await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error during commit: {e}")
            await session.rollback()
            raise

    @classmethod
    async def rollback(cls, session: AsyncSession):
        """
        Roll back a transaction.
        
        Args:
            session: The database session
        """
        await session.rollback()

async def get_db() -> AsyncSession:
    """Dependency to get the async database session."""
    async with Database.get_session_factory()() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise SQLAlchemyError(f"Database error: {str(e)}")
        finally:
            await session.close()
