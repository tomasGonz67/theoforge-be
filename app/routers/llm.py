from fastapi import APIRouter, HTTPException
from openai import OpenAI
import os

from app.database import Neo4jService
from dotenv import load_dotenv

router = APIRouter(prefix="/llm", tags=["llm"])
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_relevant_context(query_embedding):
    """
    Neo4j context is used with query embeddings to find similar embeddings and fetch related entities and relationships.
    Returns relevant text with gen. LLM (OpenAI).
    """

    query = """
    MATCH (n:Document)
    WITH n, cosineSimilarity(n.embedding, $queryEmbedding) AS similarity
    ORDER BY similarity DESC
    LIMIT 5
    RETURN n.text AS context
    """
    results = Neo4jService.execute_query(query, {"queryEmbedding": query_embedding})
    return " ".join([record["context"] for record in results])


@router.post("/generate-response")
def generate_response(user_input: str, query_embedding: list[float]):
    try:
        context = get_relevant_context(query_embedding)

        prompt = f"""
        Context: {context}
        Question: {user_input}
        Answer:
        """

        response = client.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "You are an expert AI assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=300
        )

        return {"response": response["choices"][0]["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
