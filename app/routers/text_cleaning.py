import os
import json
from typing import Dict, Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI

from app.operations.qdrant import qdrant_service
from app.operations.neo4j import Neo4jKnowledgeGraphLoader
from app.schemas.neo4j import KnowledgeGraphInput

logger = logging.getLogger(__name__)

class TextCleaningService:
    def __init__(self, api_key: str = None):
        """Initialize the service with an OpenAI API key and async client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set it in the .env file or pass it explicitly.")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def process_text(self, raw_text: str) -> Dict[str, Any]:
        """Process raw text, store embeddings in Qdrant, and load graph data into Neo4j."""
        qdrant_status = "pending"
        neo4j_status = "pending"
        error_message = None
        normalized_data = {}

        try:
            cleaned_text = self._basic_cleaning(raw_text)

            structured_data = await self._extract_entities_and_relationships(cleaned_text)
            logger.info(f"--- Data after _extract_entities_and_relationships ---\n{json.dumps(structured_data, indent=2)}")

            enhanced_data = await self._enhance_with_context(structured_data)
            logger.info(f"--- Data after _enhance_with_context ---\n{json.dumps(enhanced_data, indent=2)}")

            normalized_data = self._normalize_keys(enhanced_data)

            if 'entities' in normalized_data and normalized_data['entities']:
                try:
                    # Pass a copy to _generate_embeddings to avoid modifying normalized_data in-place
                    entities_to_embed = [entity.copy() for entity in normalized_data['entities']]
                    entities_with_embeddings = await self._generate_embeddings(entities_to_embed)
                    if entities_with_embeddings:
                         # Use the result containing embeddings only for Qdrant
                         await qdrant_service.upsert_vectors(entities_with_embeddings)
                         qdrant_status = "success"
                    else:
                        logger.warning("--- Embedding generation resulted in empty list, skipping Qdrant upsert ---")
                        qdrant_status = "failed"
                except Exception as e:
                    logger.error(f"Error during embedding generation or Qdrant upsert: {e}")
                    qdrant_status = "failed"
            else:
                logger.info("--- No entities found in normalized data to generate embeddings for. ---")
                qdrant_status = "skipped"

            try:
                neo4j_result = Neo4jKnowledgeGraphLoader.load_knowledge_graph(normalized_data)
                if neo4j_result.get("status") == "error":
                     neo4j_status = "failed"
                     error_message = neo4j_result.get("message", "Neo4j loading failed")
                     logger.error(f"Neo4j loading reported an error: {error_message}")
                else:
                    neo4j_status = "success"
                    logger.info("Successfully loaded data into Neo4j.")

            except Exception as e:
                neo4j_status = "failed"
                error_message = f"Neo4j loading failed: {str(e)}"
                logger.error(error_message)

        except Exception as e:
            logger.exception("An unexpected error occurred during text processing.") # Log full traceback
            error_message = f"An unexpected error occurred: {str(e)}"
            # Determine which steps failed based on where the exception occurred
            if qdrant_status == "pending": qdrant_status = "failed"
            if neo4j_status == "pending": neo4j_status = "failed"

        # Return status of operations
        return {
            "qdrant_status": qdrant_status,
            "neo4j_status": neo4j_status,
            "error_message": error_message # Provide error details if any step failed
        }


    def _basic_cleaning(self, text: str) -> str:
        """Perform basic text cleaning."""
        return " ".join(text.split())

    async def _extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """Use GPT to extract entities and their relationships from text."""
        prompt = f"""
       Extract important entities and their relationships from the following text:
       
       {text}
       
       For each entity, provide:
       1. Entity name
       2. Entity type (person, organization, product, concept, etc.)
       3. Key attributes mentioned
       
       For relationships, provide:
       1. Source entity
       2. Relationship type/verb
       3. Target entity
       
       Format as JSON with 'entities' and 'relationships' arrays.
       """

        client = self.client

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content
        print("API Response Content:", content)  

        if "```" in content:
            start_idx = content.find("```") + 3
            if content[start_idx:].find("\n") >= 0:
                start_idx = start_idx + content[start_idx:].find("\n") + 1
            end_idx = content.rfind("```")
            if start_idx < end_idx:
                content = content[start_idx:end_idx].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")

    async def _enhance_with_context(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add implied context to the structured data."""
        data_str = json.dumps(structured_data, indent=2)

        prompt = f"""
       Review the following extracted entities and relationships:
       
       {data_str}
       
       Enhance this data by:
       1. Adding any missing but implied relationships
       2. Adding common knowledge about entities that's relevant (e.g., if Zuckerberg is mentioned, add relationship to Facebook if missing)
       3. Resolving pronouns (he/she/they) to specific entities where possible
       4. Inferring entity types for unclassified entities
       
       Return the enhanced complete JSON with all original and new data.
       """
        client = self.client

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content
        print("API Response Content:", content)  

        if "```" in content:
            start_idx = content.find("```") + 3
            if content[start_idx:].find("\n") >= 0:
                start_idx = start_idx + content[start_idx:].find("\n") + 1
            end_idx = content.rfind("```")
            if start_idx < end_idx:
                content = content[start_idx:end_idx].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")

    def _normalize_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize keys in entities and relationships to a standard format, handling variations in input keys."""
        normalized_entities = []
        normalized_relationships = []
        logger.info("Starting _normalize_keys...")

        if 'entities' in data and isinstance(data['entities'], list):
            logger.info(f"Processing {len(data['entities'])} entities from input data...")
            for entity in data['entities']:
                if not isinstance(entity, dict):
                    logger.warning(f"Skipping non-dict entity: {entity}")
                    continue

                # Handle variations for entity name and type
                entity_name = entity.get('name') or entity.get('entity_name')
                entity_type = entity.get('type') or entity.get('entity_type', 'ENTITY') # Default if neither is found

                if not entity_name:
                    logger.warning(f"Skipping entity due to missing 'name' or 'entity_name': {entity}")
                    continue

                # Handle variations for attributes
                attributes_list = entity.get('attributes') or entity.get('key_attributes', [])
                try:
                    # Ensure attributes are strings before joining/dumping
                    attributes_json = json.dumps([str(attr) for attr in attributes_list]) if attributes_list else None
                except TypeError:
                    logger.error(f"Error serializing attributes for entity {entity_name}: {attributes_list}")
                    attributes_json = json.dumps([]) # Default to empty list on error

                norm_entity = {
                    'text': entity_name,
                    'label': entity_type.upper(),
                    'attributes': attributes_json
                }
                normalized_entities.append(norm_entity)
                logger.debug(f"Normalized entity: {norm_entity}")

        if 'relationships' in data and isinstance(data['relationships'], list):
            logger.info(f"Processing {len(data['relationships'])} relationships from input data...")
            for rel in data['relationships']:
                if not isinstance(rel, dict):
                    logger.warning(f"Skipping non-dict relationship: {rel}")
                    continue
                
                # Handle variations for relationship keys
                source = rel.get('source') or rel.get('source_entity')
                target = rel.get('target') or rel.get('target_entity')
                relationship_type = rel.get('relationship') or rel.get('relationship_type')

                if not source or not target or not relationship_type:
                    logger.warning(f"Skipping relationship due to missing keys (source/source_entity, target/target_entity, relationship/relationship_type): {rel}")
                    continue

                norm_rel = {
                    'subject': source,
                    'predicate': relationship_type,
                    'object': target
                }
                normalized_relationships.append(norm_rel)
                logger.debug(f"Normalized relationship: {norm_rel}")

        logger.info(f"Finished _normalize_keys. Result: entities={len(normalized_entities)}, relationships={len(normalized_relationships)}")
        return {"entities": normalized_entities, "relationships": normalized_relationships}

    async def _generate_embeddings(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for each entity using AsyncOpenAI."""
        texts_to_embed = [entity.get('text', '') for entity in entities if entity.get('text')]
        if not texts_to_embed:
            for entity in entities:
                entity['embedding'] = None
            return entities

        try:
            response = await self.client.embeddings.create(
                input=texts_to_embed,
                model="text-embedding-3-small" 
            )
            embedding_map = {text: data.embedding for text, data in zip(texts_to_embed, response.data)}

            for entity in entities:
                entity['embedding'] = embedding_map.get(entity.get('text')) 

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}") 
            for entity in entities:
                entity['embedding'] = None

        return entities


class TextCleaningResponse(BaseModel):
    qdrant_status: str
    neo4j_status: str
    message: str = "Processing complete."
    error_details: str = None # Include specific error if needed


class TextCleaningRequest(BaseModel):
    raw_text: str


# Dependency for TextCleaningService
def get_text_cleaning_service():
    return TextCleaningService()

router = APIRouter(
    prefix="/text-cleaning",
    tags=["Text Cleaning"],
    responses={404: {"description": "Not found"}},
)

text_cleaning_service = get_text_cleaning_service()

@router.post("/clean", response_model=TextCleaningResponse)
async def clean_text(request: TextCleaningRequest, service: TextCleaningService = Depends(get_text_cleaning_service)):
    """
    Endpoint to clean text, extract entities/relationships, store in Qdrant, and load into Neo4j.
    """
    try:
        # Use request.raw_text instead of request.text
        result = await service.process_text(request.raw_text)

        # Determine overall status and message
        overall_status = status.HTTP_200_OK
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing text: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during text cleaning: {str(e)}")