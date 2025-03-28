from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import importlib
import pkgutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, Database, DbService, Neo4jDatabase, Neo4jService
from app.routers import auth, guest, resource
from app.routers.dependencies import ParagraphRequest, Neo4jKnowledgeGraphGenerator

# Get database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    Database.initialize(database_url)

# Get Neo4j connection details from environment variables
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

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
    
    yield
    
    # Cleanup: close Neo4j connection
    Neo4jDatabase.close()

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

@app.get("/neo4j/hello-world")
def neo4j_hello_world():
    """
    Creates a node in Neo4j with a "Hello, World!" message and retrieves it.
    This is a simple test to confirm Neo4j connectivity.
    """
    try:
        # Create a node with a "Hello, World!" message
        create_query = """
        CREATE (message:Message {text: 'Hello, World!'})
        RETURN message
        """
        Neo4jService.execute_query(create_query)
        
        # Retrieve the message
        get_query = """
        MATCH (message:Message)
        WHERE message.text = 'Hello, World!'
        RETURN message.text AS message
        """
        result = Neo4jService.execute_query(get_query)
        
        if result and len(result) > 0:
            return {"message": result[0]["message"]}
        else:
            return {"error": "Message not found in Neo4j"}
    except Exception as e:
        return {"error": f"Neo4j operation failed: {str(e)}"}


CSV_FOLDER = "app/neo4j"

@app.get("/csv/{filename}")
async def get_csv(filename: str):
    """Serving the example CSV files for Neo4j to import"""
    file_path = os.path.join(CSV_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv")
    return {"error": "File not found"}

@app.get("/neo4j/user-example")
def neo4j_user_example():
    
    # Creates multiple nodes and relationships in Neo4j with example CSV data.
    # This is a simple test to confirm Neo4j connectivity.
    
    try:
        # Neo4jDatabase.create_constraints()
        Neo4jDatabase.import_csv()
    except Exception as e:
        return {"error": f"Neo4j operation failed: {str(e)}"}

@app.post("/neo4j/create-knowledge-graph")
def create_paragraph_knowledge_graph(request: ParagraphRequest):
    """
    Create a knowledge graph from an input paragraph.
    
    This endpoint:
    1. Preprocesses the input text
    2. Extracts entities and relationships
    3. Generates Neo4j Cypher queries
    4. Executes the queries to create the knowledge graph

    EXAMPLE:
    "Keith founded TheoForge. Also, Keith creates apps. Meanwhile, apps use AI. OpenAI makes models and Google makes AI. TheoForge uses AI. Then, students are programming TheoForge."
        
        - This will create four entities: Keith, TheoForge, Apps, and AI.
        - 3 relationships are made, Keith --> TheoForge, Keith --> Apps, and Apps --> AI
    """
    try:
        preprocessed_text = Neo4jKnowledgeGraphGenerator.preprocess_text(request.text)
        knowledge_elements = Neo4jKnowledgeGraphGenerator.extract_knowledge_elements(preprocessed_text)
        # Generate Neo4j queries
        cypher_queries = Neo4jKnowledgeGraphGenerator.create_neo4j_knowledge_graph(knowledge_elements)
        
        for query in cypher_queries:
            Neo4jService.execute_query(query)
        
        return {
            "status": "Success",
            "entities": knowledge_elements.get("entities", []),
            "relationships": knowledge_elements.get("relationships", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge graph creation failed: {str(e)}")

@app.get("/neo4j/verify-entities-and-relationships")
def verify_graph():
    """
    Verify entities and relationships in the graph
    """
    verify_entities_query = """
    MATCH (n:Entity) RETURN n.text AS text, n.type AS type
    """
    verify_relationships_query = """
    MATCH (a)-[r]->(b) 
    RETURN a.text AS source, type(r) AS relationship_type, b.text AS target
    """
    
    entities = Neo4jService.execute_query(verify_entities_query)
    relationships = Neo4jService.execute_query(verify_relationships_query)
    
    return {
        "entities": entities,
        "relationships": relationships
    }

@app.delete("/neo4j/delete-all")
async def delete_all():
    """Delete all nodes and relationships in Neo4j database"""
    try:
        result = Neo4jService.execute_query("MATCH (n) DETACH DELETE n")

        return {
            "status": "Success",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
