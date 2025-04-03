import json
from dotenv import load_dotenv
from openai import OpenAI
import os
from typing import Dict, List, Any

load_dotenv()

class TextCleaningService:
    def __init__(self, api_key: str = None):
        """Initialize the service with an OpenAI API key and client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set it in the .env file or pass it explicitly.")
        self.client = OpenAI(api_key=self.api_key) # Initialize client once

    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """Process raw text into clean, structured data with entities and relationships."""
        # Step 1: Basic cleaning (remove extra whitespace, fix formatting)
        cleaned_text = self._basic_cleaning(raw_text)

        # Step 2: Extract entities and relationships using GPT
        structured_data = self._extract_entities_and_relationships(cleaned_text)

        # Step 3: Enhance data with implied context
        enhanced_data = self._enhance_with_context(structured_data)

        # Step 4: Normalize keys to a consistent format
        normalized_data = self._normalize_keys(enhanced_data)

        # Step 5: Generate embeddings for entities (if any)
        if 'entities' in normalized_data and normalized_data['entities']:
             normalized_data['entities'] = self._generate_embeddings(normalized_data['entities'])

        return normalized_data

    def _basic_cleaning(self, text: str) -> str:
        """Perform basic text cleaning."""
        # Remove extra whitespace, normalize line breaks, etc.
        return " ".join(text.split())

    def _extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
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

        # Use the initialized OpenAI client
        client = self.client

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Access the content of the first choice
        content = response.choices[0].message.content
        print("API Response Content:", content)  # Debugging line

        # Extract JSON content from markdown code blocks if present
        if "```" in content:
            # Find all content between code block markers
            start_idx = content.find("```") + 3
            # Find the end of the language identifier line if it exists
            if content[start_idx:].find("\n") >= 0:
                start_idx = start_idx + content[start_idx:].find("\n") + 1
            end_idx = content.rfind("```")
            if start_idx < end_idx:
                content = content[start_idx:end_idx].strip()

        try:
            # Parse the response content as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")

    def _enhance_with_context(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add implied context to the structured data."""
        # Convert to string to send to GPT
        data_str = str(structured_data)
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
        # Use the initialized OpenAI client
        client = self.client

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Access the content of the first choice
        content = response.choices[0].message.content
        print("API Response Content:", content)  # Debugging line

        # Extract JSON content from markdown code blocks if present
        if "```" in content:
            # Find all content between code block markers
            start_idx = content.find("```") + 3
            # Find the end of the language identifier line if it exists
            if content[start_idx:].find("\n") >= 0:
                start_idx = start_idx + content[start_idx:].find("\n") + 1
            end_idx = content.rfind("```")
            if start_idx < end_idx:
                content = content[start_idx:end_idx].strip()

        try:
            # Parse the response content as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")

    def _normalize_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize keys in entities and relationships to a standard format."""
        normalized_entities = []
        if "entities" in data and isinstance(data["entities"], list):
            for entity in data["entities"]:
                if not isinstance(entity, dict): continue # Skip non-dict items
                norm_entity = {
                    'name': entity.get('name') or entity.get('entityName') or entity.get('entity_name', ''),
                    'type': entity.get('type') or entity.get('entityType') or entity.get('entity_type', 'Entity'),
                    'attributes': entity.get('attributes') or entity.get('keyAttributes') or entity.get('key_attributes', [])
                }
                # Preserve embedding if it exists from a previous step (though unlikely here)
                if 'embedding' in entity:
                    norm_entity['embedding'] = entity['embedding']
                normalized_entities.append(norm_entity)

        normalized_relationships = []
        if "relationships" in data and isinstance(data["relationships"], list):
             for rel in data["relationships"]:
                 if not isinstance(rel, dict): continue # Skip non-dict items
                 norm_rel = {
                     'source': rel.get('source') or rel.get('sourceEntity') or rel.get('source_entity', ''),
                     'target': rel.get('target') or rel.get('targetEntity') or rel.get('target_entity', ''),
                     'relationship': rel.get('relationship') or rel.get('relationshipType') or rel.get('relationship_type', 'RELATED_TO')
                 }
                 normalized_relationships.append(norm_rel)

        return {"entities": normalized_entities, "relationships": normalized_relationships}

    def _generate_embeddings(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for each entity using OpenAI."""
        # Ensure client is initialized (redundant if __init__ always runs first, but safe)
        if not hasattr(self, 'client'):
             self.client = OpenAI(api_key=self.api_key)

        texts_to_embed = [entity.get('name', '') for entity in entities if entity.get('name')]
        if not texts_to_embed:
             # Add None embeddings if no text to embed
             for entity in entities:
                 entity['embedding'] = None
             return entities

        try:
            response = self.client.embeddings.create(
                input=texts_to_embed,
                model="text-embedding-3-small" # Use a standard embedding model
            )
            embedding_map = {text: data.embedding for text, data in zip(texts_to_embed, response.data)}

            for entity in entities:
                entity['embedding'] = embedding_map.get(entity.get('name')) # Assign embedding or None

        except Exception as e:
            print(f"Error generating embeddings: {e}") # Log error
            # Assign None to all embeddings on error
            for entity in entities:
                entity['embedding'] = None

        return entities