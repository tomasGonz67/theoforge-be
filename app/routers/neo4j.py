from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import json
from typing import Optional

from app.database import Neo4jDatabase, Neo4jService
from app.operations.neo4j import Neo4jKnowledgeGraphLoader
from app.operations.philosophers import PhilosophersGraphLoader
from app.schemas.neo4j import KnowledgeGraphInput, KnowledgeGraphResponse, VerifyGraphResponse
from app.schemas.philosophers import PhilosophersGraph, PhilosopherFilterParams

# Router for Neo4j operations
router = APIRouter(prefix="/neo4j", tags=["Neo4j"])

@router.get("/neo4j/hello-world")
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

@router.get("/csv/{filename}")
async def get_csv(filename: str):
    """Serving the example CSV files for Neo4j to import"""
    file_path = os.path.join(CSV_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv")
    return {"error": "File not found"}

@router.get("/neo4j/user-example")
def neo4j_user_example():
    
    # Creates multiple nodes and relationships in Neo4j with example CSV data.
    # This is a simple test to confirm Neo4j connectivity.
    
    try:
        # Neo4jDatabase.create_constraints()
        Neo4jDatabase.import_csv()
    except Exception as e:
        return {"error": f"Neo4j operation failed: {str(e)}"}

@router.post("/load-knowledge-graph", response_model=KnowledgeGraphResponse)
def load_knowledge_graph_endpoint(request: KnowledgeGraphInput):
    """
    Load structured knowledge graph data (entities and relationships) into Neo4j.

    This endpoint accepts a JSON object containing lists of entities and relationships
    and uses the Neo4jKnowledgeGraphLoader to persist them in the database.
    """
    try:
        # Load data using the Neo4jKnowledgeGraphLoader
        result = Neo4jKnowledgeGraphLoader.load_knowledge_graph(request.model_dump())

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Knowledge graph loading failed"))

        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge graph loading failed: {str(e)}")

@router.get("/verify-graph", response_model=VerifyGraphResponse)
def verify_graph_endpoint():
    """
    Verify entities and relationships in the graph
    """
    # Query to fetch all nodes with their text and labels
    # Query to fetch all nodes with their text, labels, and embedding
    verify_entities_query = """
    MATCH (n) WHERE n.text IS NOT NULL RETURN n.text AS text, labels(n) AS labels, n.embedding AS embedding
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

@router.delete("/neo4j/delete-all")
async def delete_all():
    """Delete all nodes and relationships in Neo4j database"""
    try:
        Neo4jService.execute_query("MATCH (n) DETACH DELETE n")

        return {
            "status": "Success",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Philosophers Knowledge Graph Endpoints

@router.post("/philosophers/import")
async def import_philosophers_json(data: PhilosophersGraph):
    """
    Import philosophers knowledge graph data from JSON.
    
    This endpoint accepts the complete philosophers graph JSON structure and imports it into Neo4j.
    """
    try:
        result = PhilosophersGraphLoader.import_philosophers_from_json(data.model_dump())
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to import philosophers data"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import philosophers data: {str(e)}")


@router.post("/philosophers/import-file")
async def import_philosophers_file(file_path: str):
    """
    Import philosophers knowledge graph data from a JSON file.
    
    This endpoint takes a file path to a JSON file containing the philosophers graph data.
    """
    try:
        result = PhilosophersGraphLoader.import_philosophers_from_file(file_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to import philosophers data from file"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import philosophers from file: {str(e)}")


@router.post("/philosophers/import-default")
async def import_philosophers_default():
    """
    Import philosophers knowledge graph data from the default JSON file at public/data/philosophers.json.
    
    This endpoint requires no parameters and automatically imports from the predefined file.
    """
    try:
        # Define the path to the default philosophers.json file
        import os
        from pathlib import Path
        
        # Look for the file in the app/data directory, which is mounted in the Docker container
        file_path = os.path.join("app", "data", "philosophers.json")
        # If running locally outside Docker
        if not os.path.exists(file_path):
            # Try with just the directory name
            file_path = os.path.join("data", "philosophers.json")
            
        # Get absolute path for better error reporting
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Default philosophers file not found at {file_path}")
        
        result = PhilosophersGraphLoader.import_philosophers_from_file(file_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to import philosophers data"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import philosophers: {str(e)}")


@router.get("/philosophers-graph", response_model=PhilosophersGraph)
async def get_philosophers_graph():
    """
    Get the complete philosophers knowledge graph.
    
    Returns the full graph with nodes and links in the format expected by the frontend visualization.
    """
    try:
        graph_data = PhilosophersGraphLoader.get_philosophers_graph()
        
        if graph_data is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve philosophers graph data")
            
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve philosophers graph: {str(e)}")