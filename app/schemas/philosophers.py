from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class PhilosopherNode(BaseModel):
    """Model representing a philosopher node in the knowledge graph"""
    id: str
    name: str
    era: str
    community: int
    influenceScore: float
    description: str
    contributions: List[str] = Field(default_factory=list)
    schools: Optional[List[str]] = None
    key_ideas: Optional[List[str]] = None


class PhilosopherLink(BaseModel):
    """Model representing a relationship between philosophers"""
    source: str
    target: str
    relation: str
    strength: float


class PhilosophersGraph(BaseModel):
    """Complete philosophers knowledge graph model"""
    nodes: List[PhilosopherNode] = Field(default_factory=list)
    links: List[PhilosopherLink] = Field(default_factory=list)


class PhilosopherListResponse(BaseModel):
    """Response model for list of philosophers"""
    philosophers: List[PhilosopherNode]


# Query parameter models for filtering philosophers
class PhilosopherFilterParams(BaseModel):
    """Query parameters for filtering philosophers"""
    era: Optional[str] = None
    min_influence: Optional[float] = None
    max_influence: Optional[float] = None
    name_contains: Optional[str] = None
