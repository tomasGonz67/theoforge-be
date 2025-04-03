from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.database import Neo4jDatabase, Neo4jService
from app.operations.neo4j import ParagraphRequest, Neo4jKnowledgeGraphGenerator

# Create a router for neo4j endpoints
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

@router.post("/neo4j/create-knowledge-graph")
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

@router.get("/neo4j/verify-entities-and-relationships")
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