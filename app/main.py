from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.operations.qdrant import qdrant_service

from app.database import Base, Database, DbService, Neo4jDatabase, Neo4jService
from app.routers import auth, guest, resource, neo4j, llm, text_cleaning

# Get database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    Database.initialize(database_url)

# Get Neo4j connection details from environment variables
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database is initialized
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Initialize Neo4j connection
    if neo4j_uri and neo4j_user and neo4j_password:
        try:
            Neo4jDatabase.initialize(neo4j_uri, neo4j_user, neo4j_password)
            print("Neo4j connection established successfully")
        except Exception as e:
            print(f"Failed to initialize Neo4j connection: {e}")
    
    # Initialize Qdrant connection and collection
    logger.info("Application startup: Initializing Qdrant connection and collection...")
    try:
        await qdrant_service.initialize_collection()
        logger.info("Qdrant initialization complete.")
    except Exception as e:
        logger.error(f"Qdrant initialization failed: {e}")
        # Depending on the application's needs, you might want to prevent startup
        # For now, we log the error and continue
    
    yield
    
    # Cleanup: close Neo4j connection
    Neo4jDatabase.close()
    
    # Close Qdrant client
    logger.info("Application shutdown: Closing Qdrant client...")
    await qdrant_service.close()
    logger.info("Qdrant client closed.")

app = FastAPI(title="TheoForge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend origin
    allow_credentials=True,  # Required for auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(guest.router)
app.include_router(resource.router)
app.include_router(neo4j.router)
app.include_router(llm.router)
app.include_router(text_cleaning.router)

@app.get("/")
async def root():
    return {"message": "Hello World test"}

@app.get("/health")
async def health():
    """
    Health check endpoint that verifies application and database health asynchronously.
    Uses the same async database connection pattern as the rest of the application.
    """
    db_status = "not checked"
    
    if database_url:
        # Create a session for this request
        async_session_factory = Database.get_session_factory()
        async with async_session_factory() as session:
            try:
                # use async query execution
                result = await DbService.execute_query(session, text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    db_status = "connected"
                else:
                    db_status = "error: unexpected query result"
            except SQLAlchemyError as e:
                db_status = f"error: {str(e)}"
            finally:
                await session.close()
    else:
        db_status = "no database configured"
    
    return {
        "status": "healthy",
        "database": db_status
    }


@app.get("/neo4j/health")
def neo4j_health():
    """
    Health check endpoint that verifies Neo4j connection.
    """
    try:
        result = Neo4jService.execute_query("RETURN 1 AS n")
        if result and len(result) > 0 and result[0]["n"] == 1:
            return {"status": "connected"}
        else:
            return {"status": "error", "message": "Unexpected response from Neo4j"}
    except Exception as e:
        return {"status": "error", "message": str(e)}