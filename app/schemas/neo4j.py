from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EntitySchema(BaseModel):
    text: str
    label: Optional[str] = 'Entity' # Default label if not provided
    # embedding: Optional[List[float]] = None # Removed - handled separately
    attributes: Optional[str] = None # Add optional field for serialized attributes

class RelationshipSchema(BaseModel):
    subject: str
    predicate: str
    object: str

class KnowledgeGraphInput(BaseModel):
    """Input schema for loading structured knowledge graph data."""
    entities: List[EntitySchema] = Field(default_factory=list)
    relationships: List[RelationshipSchema] = Field(default_factory=list)

class KnowledgeGraphResponse(BaseModel):
    """Response schema for knowledge graph operations."""
    status: str
    nodes_processed: Optional[int] = None # Approx. count of nodes processed
    relationships_processed: Optional[int] = None # Approx. count of relationships processed
    message: Optional[str] = None

class VerifyGraphResponse(BaseModel):
    """Response schema for verifying graph content."""
    entities: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[Dict[str, Any]]] = None