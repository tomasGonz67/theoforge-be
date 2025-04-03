from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
import logging

# Import from the sub-package within 'app'
from app.text_to_cleaning.text_cleaning import TextCleaningService

from app.operations.neo4j import Neo4jKnowledgeGraphLoader
from app.database import get_db # If needed for other dependencies, though not directly used here
from settings.config import settings # Corrected import path for settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

class TextInput(BaseModel):
    raw_text: str

@router.post("/process-and-load")
async def process_and_load_text(text_input: TextInput = Body(...)):
    """
    Processes raw text: cleans, extracts entities/relationships, generates embeddings,
    and loads the resulting knowledge graph into Neo4j.
    """
    # Removed the check for TextCleaningService being None.
    # If the import above fails, the application will not start.

    try:
        # 1. Initialize the Text Cleaning Service
        # Consider how the API key is best managed - direct env var read is simple for now
        cleaning_service = TextCleaningService()

        # 2. Process the text (clean, extract, enhance, embed)
        logger.info("Starting text processing...")
        knowledge_elements = cleaning_service.process_text(text_input.raw_text)
        logger.info("Text processing completed.")
        # Log the actual data structure returned by the cleaning service
        logger.info(f"Knowledge Elements from Cleaning Service: {knowledge_elements}")

        # Check if processing returned expected structure
        if not knowledge_elements or not isinstance(knowledge_elements, dict):
             logger.error(f"Text processing returned unexpected data: {knowledge_elements}")
             raise HTTPException(status_code=500, detail="Text processing failed to return valid structured data.")

        # 3. Load the knowledge graph into Neo4j
        logger.info("Starting Neo4j knowledge graph loading...")
        load_status = Neo4jKnowledgeGraphLoader.load_knowledge_graph(knowledge_elements)
        logger.info(f"Neo4j loading completed with status: {load_status.get('status')}")

        # 4. Return the result from the loading step
        if load_status.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"Failed to load data into Neo4j: {load_status.get('message')}")

        return load_status

    except ValueError as ve:
        logger.error(f"Configuration or Value Error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception("An unexpected error occurred during text processing and loading.") # Log full traceback
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")