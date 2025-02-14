import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Basic test to ensure the API is working
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

# TODO: Add more tests as we implement features 