import json
from dotenv import load_dotenv
from openai import OpenAI
import os
from typing import Dict, List, Any

load_dotenv()

class TextCleaningService:
    def __init__(self, api_key: str = None):
        """Initialize the service with an OpenAI API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set it in the .env file or pass it explicitly.")
        
    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """Process raw text into clean, structured data with entities and relationships."""
        # Step 1: Basic cleaning (remove extra whitespace, fix formatting)
        cleaned_text = self._basic_cleaning(raw_text)
        
        # Step 2: Extract entities and relationships using GPT
        structured_data = self._extract_entities_and_relationships(cleaned_text)
        
        # Step 3: Enhance data with implied context
        enhanced_data = self._enhance_with_context(structured_data)
        
        return enhanced_data
    
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
        
        # Initialize the OpenAI client
        client = OpenAI(api_key=self.api_key)
        
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
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")
        
    def _enhance_with_context(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add implied context to the structured data."""
        # Convert to string to send to GPT
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
        # Initialize the OpenAI client
        client = OpenAI(api_key=self.api_key)
        
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
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI API: {content}\nError: {str(e)}")