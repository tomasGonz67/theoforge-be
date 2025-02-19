# Database configuration and session management
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Database:
    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, database_url: str, echo: bool = False):
        """Initialize the async engine and sessionmaker."""
        if cls._engine is None:  # Ensure engine is created once
            cls._engine = create_async_engine(database_url, echo=echo, future=True)
            cls._session_factory = sessionmaker(
                bind=cls._engine, class_=AsyncSession, expire_on_commit=False, future=True
            )
    
    @classmethod
    def get_session(cls):
        """Get a new session."""
        if cls._session_factory is None:
            raise ValueError("Database not initialized")
        return cls._session_factory()

# TODO: Database URL configuration