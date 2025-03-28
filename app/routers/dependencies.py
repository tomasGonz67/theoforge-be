from builtins import Exception
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
from jose import JWTError
from jwt import PyJWTError, ExpiredSignatureError
from typing import List, Dict, Any
from pydantic import BaseModel
import re
import spacy

from app.database import Database
from app.operations.jwt_service import decode_token
from settings.config import settings

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

        return user  # ✅ Now returning the full User object instead of just email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_settings():
    """Return application settings."""
    return settings


# Neo4j Knowledge Graph Creation
class ParagraphRequest(BaseModel):
    text: str

class Neo4jKnowledgeGraphGenerator:
    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocess the input text by removing extra whitespaces and cleaning up punctuation."""
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_knowledge_elements(text: str) -> Dict[str, List[Any]]:
        """Use spaCy to extract key elements from the text for building a knowledge graph."""
        nlp = spacy.load("en_core_web_sm")
        nlp.add_pipe("merge_entities")
        
        # Process the text
        doc = nlp(text)
        entities = []
        relationships = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text.strip(),
                "label": ent.label_
            })
        
        for token in doc:
            if token.pos_ == "NOUN" and not any(token.text == ent['text'] for ent in entities):
                entities.append({
                    "text": token.text.strip(),
                    "label": "COMMON_NOUN"
                })
        
        # Extract subject-verb-object relationships
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == "VERB":
                    subject = None
                    objects = []
                    
                    for child in token.children:
                        if child.dep_ in ["nsubj", "nsubjpass"]:
                            subject = " ".join([t.text for t in child.subtree]).strip()
                        
                        if child.dep_ in ["dobj", "pobj", "iobj"]:
                            obj = " ".join([t.text for t in child.subtree]).strip()
                            objects.append(obj)
                    
                    # Create relationships for each subject-object pair
                    if subject and objects:
                        for obj in objects:
                            relationships.append({
                                "subject": subject,
                                "predicate": token.lemma_,
                                "object": obj
                            })
        
        # Remove duplicates
        entities = list({v['text']: v for v in entities}.values())
        relationships = list({(r['subject'], r['predicate'], r['object']): r for r in relationships}.values())
        
        return {
            "entities": entities,
            "relationships": relationships
        }


    @staticmethod
    def create_neo4j_knowledge_graph(knowledge_elements: Dict[str, List[Any]]) -> List[str]:
        """Generate Cypher queries to create a knowledge graph in Neo4j."""
        queries = []
        
        # Create entity nodes with sanitized text
        for entity in knowledge_elements.get("entities", []):
            safe_text = entity['text'].replace("'", "\\'")
            create_entity_query = f"""
            MERGE (e:Entity {{text: '{safe_text}', type: '{entity['label']}'}})
            """
            queries.append(create_entity_query)
        
        # Create relationships between entities
        for relationship in knowledge_elements.get("relationships", []):
            safe_subject = relationship['subject'].replace("'", "\\'")
            safe_object = relationship['object'].replace("'", "\\'")
            safe_predicate = relationship['predicate'].replace("'", "\\'").upper().replace(" ", "_")

            create_relationship_query = f"""
            MATCH (subject:Entity {{text: '{safe_subject}'}})
            MATCH (object:Entity {{text: '{safe_object}'}})
            MERGE (subject)-[:{safe_predicate}]->(object)
            """
            queries.append(create_relationship_query)
        
        return queries