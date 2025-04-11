from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
from app.database import Database, Neo4jService
from app.operations.jwt_service import decode_token
from settings.config import settings
from app.operations.qdrant import qdrant_service
import logging
import json

logger = logging.getLogger(__name__)

# Create OAuth2PasswordBearer for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_db() -> AsyncSession:
    """Dependency that provides a database session for each request."""
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        finally:
            await session.close()

# Retrieve current user from access_token in Authorization header
from app.models.user import User
from app.operations.user import UserRepository

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Extract the current user from JWT in Authorization header and return the full user object."""
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user  # Now returning the full User object instead of just email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_settings():
    """Return application settings."""
    return settings

async def get_relevant_context(query_embedding: list[float], top_k: int = 5) -> str:
    """Retrieves relevant context by searching Qdrant and then querying Neo4j."""
    try:
        # 1. Search Qdrant for similar texts
        logger.info(f"Searching Qdrant with top_k={top_k}...")
        # Use the client's search method directly
        search_result = await qdrant_service.client.search(
            collection_name=qdrant_service.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True  # Ensure payload (including 'text') is returned
        )
        logger.info(f"Qdrant search returned {len(search_result)} results.")

        relevant_texts = [hit.payload['text'] for hit in search_result if hit.payload and 'text' in hit.payload]
        logger.info(f"Extracted texts from Qdrant results: {relevant_texts}")
        if not relevant_texts:
            logger.warning("No relevant texts found in Qdrant.")
            return "No relevant documents found in Qdrant."

        # 2. Query Neo4j using the retrieved texts
        logger.info(f"Querying Neo4j with texts: {relevant_texts}")
        # Fetch nodes matching the texts and their direct neighbors/relationships
        query = """
        MATCH (d:Document)
        WHERE d.text IN $entityTexts
        OPTIONAL MATCH (d)-[r]-(neighbor)
        RETURN d.text AS nodeText, labels(d) AS nodeLabels, d.attributes AS nodeAttributes, 
               type(r) AS relationshipType, 
               neighbor.text AS neighborText, labels(neighbor) AS neighborLabels, neighbor.attributes AS neighborAttributes
        LIMIT 20 // Limit the total number of paths returned for context brevity
        """
        neo4j_results = Neo4jService.execute_query(query, {"entityTexts": relevant_texts})
        logger.info(f"Neo4j query results: {neo4j_results}")

        # Format the context string from Neo4j results
        context_parts = set() # To avoid duplicate entries

        for record in neo4j_results:
            # Extract data, providing defaults
            node_text = record.get('nodeText', 'Unknown Node')
            node_labels = record.get('nodeLabels', ['Unknown'])
            node_attrs_json_str = record.get('nodeAttributes') # JSON string or None
            relationship_type = record.get('relationshipType', 'RELATED_TO')
            neighbor_text = record.get('neighborText', 'Unknown Neighbor')
            neighbor_labels = record.get('neighborLabels', ['Unknown'])
            neighbor_attrs_json_str = record.get('neighborAttributes') # JSON string or None

            try:
                # Attributes are stored as JSON strings in Neo4j
                node_attrs = json.loads(node_attrs_json_str) if node_attrs_json_str else []
                neighbor_attrs = json.loads(neighbor_attrs_json_str) if neighbor_attrs_json_str else []

                # Format attributes for the context string
                node_attrs_str = ", ".join(node_attrs) if node_attrs else "No attributes"
                neighbor_attrs_str = ", ".join(neighbor_attrs) if neighbor_attrs else "No attributes"

                # Format the node part
                node_context = f"Node: {node_text} (Labels: {', '.join(node_labels)}, Attributes: {node_attrs_str})"
                context_parts.add(node_context) # Use set to avoid duplicate node entries

                # Format the relationship part
                if relationship_type and neighbor_text:
                    rel_context = f"  - Relationship: ({node_text})-[{relationship_type}]->({neighbor_text} (Labels: {', '.join(neighbor_labels)}, Attributes: {neighbor_attrs_str}))"
                    context_parts.add(rel_context) # Use set to avoid duplicate relationship entries

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for node {node_text}: {e}")
                logger.error(f"Problematic node_attrs: {node_attrs_json_str}")
                logger.error(f"Problematic neighbor_attrs: {neighbor_attrs_json_str}")
                # Add basic info even if attributes fail to parse
                node_context = f"Node: {node_text} (Labels: {', '.join(node_labels)}, Attributes: Error parsing)"
                context_parts.add(node_context)
                if relationship_type and neighbor_text:
                    rel_context = f"  - Relationship: ({node_text})-[{relationship_type}]->({neighbor_text} (Labels: {', '.join(neighbor_labels)}, Attributes: Error parsing))"
                    context_parts.add(rel_context)
            except Exception as e:
                logger.error(f"Unexpected error processing record: {record} - {e}")
                # Add basic info even on unexpected errors
                node_context = f"Node: {node_text} (Labels: {', '.join(node_labels)}, Attributes: Processing error)"
                context_parts.add(node_context)
                if relationship_type and neighbor_text:
                    rel_context = f"  - Relationship: ({node_text})-[{relationship_type}]->({neighbor_text} (Labels: {', '.join(neighbor_labels)}, Attributes: Processing error))"
                    context_parts.add(rel_context)

        if not context_parts:
            logger.warning("Neo4j query returned results, but context could not be formatted.")
            return "Context found but could not be formatted."

        context_string = "\n".join(context_parts)
        logger.info(f"Formatted Context String (length {len(context_string)}):\n{context_string[:500]}...") # Log truncated context
        return context_string

    except HTTPException as e:
        # Re-raise HTTPExceptions if qdrant_service raises one (e.g., collection not found)
        raise e
    except Exception as e:
        logger.error(f"Error getting relevant context: {e}", exc_info=True)
        # Return a generic error message or raise an HTTPException
        # For now, returning a simple string
        return f"Error retrieving context: {str(e)}"