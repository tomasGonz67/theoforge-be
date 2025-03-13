from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from threading import Lock
from builtins import ValueError, bool
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
import os
from neo4j import GraphDatabase

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

class Neo4jDatabase:
    """
    Neo4j database connection handler
    """
    _driver = None

    @classmethod
    def initialize(cls, uri, user, password):
        """Initialize Neo4j connection"""
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connectivity
            try:
                cls._driver.verify_connectivity()
            except Exception as e:
                print(f"Neo4j connection error: {e}")
                cls._driver = None
                raise

    @classmethod
    def get_driver(cls):
        """Get the Neo4j driver instance"""
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            cls.initialize(uri, user, password)
        return cls._driver

    @classmethod
    def close(cls):
        """Close the Neo4j driver connection"""
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
    """
    @classmethod
    def create_constraints(cls):
        # Create constraints for Neo4j database
        driver = cls.get_driver()
        with driver.session() as session:
            # Example constraints using example csvs
            # Unique constraint: Ensures 'User' nodes always have an 'id'
            session.run("CREATE CONSTRAINT userIdConstraint FOR (user:User) REQUIRE user.id IS UNIQUE")
            # Unique constraint: Ensures 'Group' nodes always have an 'id'
            session.run("CREATE CONSTRAINT groupIdConstraint FOR (group:Group) REQUIRE group.id IS UNIQUE")
    """
    @classmethod
    def import_csv(cls):
        """
        Import CSV files into Neo4j
            - Only used for example data
        """
        queries = [
            """
            LOAD CSV WITH HEADERS FROM 'http://localhost:8000/csv/example.users.csv' AS csvLine
            CREATE (user:User {id: toInteger(csvLine.id), name: csvLine.name, email: csvLine.email})
            """,
            """
            LOAD CSV WITH HEADERS FROM 'http://localhost:8000/csv/example.groups.csv' AS csvLine
            MERGE (country:Country {name: csvLine.country})
            CREATE (group:Group {id: toInteger(csvLine.id), name: csvLine.name})
            CREATE (group)-[:ORIGIN]->(country)
            """,
            """
            LOAD CSV WITH HEADERS FROM 'http://localhost:8000/csv/example.roles.csv' AS csvLine
            CALL {
            WITH csvLine
            MATCH (user:User {id: toInteger(csvLine.userId)}), (group:Group {id: toInteger(csvLine.groupId)})
            CREATE (user)-[:ASSIGNED_TO {role: csvLine.role}]->(group)
            } IN TRANSACTIONS OF 2 ROWS
            """
        ]

        driver = cls.get_driver()
        with driver.session() as session:
            for query in queries:
                session.run(query)

class Neo4jService:
    """
    Service for Neo4j database operations
    """
    @staticmethod
    def execute_query(query, parameters=None):
        """Execute a Cypher query and return the result"""
        driver = Neo4jDatabase.get_driver()
        with driver.session() as session:
            result = session.run(query, parameters)
            return result.data()
