from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import logging

from app.routers.dependencies import get_relevant_context

router = APIRouter(prefix="/llm", tags=["llm"])
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

@router.post("/generate-response")
async def generate_response(user_input: str):
    """
    Neo4j context is used with query embeddings to find similar embeddings and fetch related entities and relationships.
    Returns relevant text with gen. LLM (OpenAI).
    """

    try:
        # Generate query embedding from user input
        embedding_response = await client.embeddings.create(
            input=[user_input],
            model="text-embedding-3-small"
        )
        query_embedding = embedding_response.data[0].embedding

        logger.info("Calling get_relevant_context...")
        context = await get_relevant_context(query_embedding) # Use generated embedding
        logger.info(f"Context received from get_relevant_context:\n{context}")

        prompt = f"""
        Use the following context to answer the question. If the context doesn't provide the answer, say you don't have enough information.
        Context: {context}
        Question: {user_input}
        Answer:
        """
        logger.info(f"Prompt being sent to LLM:\n{prompt}")

        # Use chat completions API
        response = await client.chat.completions.create(
            model="gpt-4-turbo", # Or gpt-4o if preferred
            messages=[
                {"role": "system", "content": "You are an expert AI assistant. Use the provided context to answer the question."},
                {"role": "user", "content": prompt} # Prompt already includes context and question
            ],
            max_tokens=300
        )

        # Parse chat completions response
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
