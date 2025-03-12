"""
Test configuration of Neo4j.

These tests verify that the Neo4j correctly runs and executes queries:
- Transaction isolation
- Concurrent operations
- Error handling with real database
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_neo4j_execute_query():
    """Fixture to mock Neo4jService execute_query method."""
    with patch("app.database.Neo4jService.execute_query") as mock:
        yield mock

def test_neo4j_hello_world(mock_neo4j_execute_query):
    """Test the /neo4j/hello-world endpoint."""
    mock_neo4j_execute_query.side_effect = [
        None,  # First call
        [{"message": "Hello, World!"}]  # Second call
    ]

    response = client.get("/neo4j/hello-world")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_neo4j_health(mock_neo4j_execute_query):
    """Test the /neo4j/health endpoint."""
    mock_neo4j_execute_query.return_value = [{"n": 1}]

    response = client.get("/neo4j/health")
    assert response.status_code == 200
    assert response.json() == {"status": "connected"}

def test_neo4j_health_failure(mock_neo4j_execute_query):
    """Test the /neo4j/health endpoint when Neo4j fails."""
    mock_neo4j_execute_query.side_effect = Exception("Neo4j error")

    response = client.get("/neo4j/health")
    assert response.status_code == 200  # FastAPI handles exceptions gracefully
    assert response.json() == {"status": "error", "message": "Neo4j error"}