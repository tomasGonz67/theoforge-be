import pytest
from pydantic import ValidationError
from app.schemas.resource import ResourceBase, ResourceCreateSchema, ResourceUpdateSchema, ResourceSchema, ErrorResponse, ResourceType
import uuid

@pytest.mark.parametrize("valid_data", [
    {
        "name": "Python Guide",
        "description": "A comprehensive guide to Python.",
        "category": "Education",
        "resource_type": ResourceType.PDF,
        "tags": ["Python", "Coding"],
        "profile_picture": "https://example.com/python.png",
        "source_url": "https://example.com/python-guide",
        "file_path": "user_id/unique-file-id.pdf",
        "user_id": str(uuid.uuid4()),
        "is_public": True
    }
])
def test_valid_resource_base(valid_data):
    """Test valid resource base schema."""
    resource = ResourceBase(**valid_data)
    assert resource.name == valid_data["name"]
    assert resource.resource_type == valid_data["resource_type"]

@pytest.mark.parametrize("invalid_data", [
    {"name": "", "resource_type": "INVALID_TYPE", "user_id": "invalid-uuid"},  # Invalid type & UUID
    {"name": "Test", "resource_type": ResourceType.PDF, "user_id": str(uuid.uuid4()), "is_public": "wrong_type"}  # Wrong bool type
])
def test_invalid_resource_base(invalid_data):
    """Test invalid resource base schema validation."""
    with pytest.raises(ValidationError):
        ResourceBase(**invalid_data)

@pytest.mark.parametrize("update_data", [
    {"name": "Updated Resource", "tags": ["Updated", "FastAPI"]},
    {"description": "New description", "is_public": False}
])
def test_valid_resource_update(update_data):
    """Test valid updates to a resource."""
    resource_update = ResourceUpdateSchema(**update_data)
    for key in update_data:
        assert getattr(resource_update, key) == update_data[key]

@pytest.mark.parametrize("invalid_update_data", [
    {"resource_type": "INVALID_TYPE"},  # Invalid enum value
    {"is_public": "not-a-boolean"}  # Invalid boolean value
])
def test_invalid_resource_update(invalid_update_data):
    """Test invalid resource update schema validation."""
    with pytest.raises(ValidationError):
        ResourceUpdateSchema(**invalid_update_data)

@pytest.mark.parametrize("error_data", [
    {"error": "NotFound", "details": "Resource not found"},
    {"error": "ValidationError", "details": "Invalid input provided"}
])
def test_error_response(error_data):
    """Test error response schema."""
    error_response = ErrorResponse(**error_data)
    assert error_response.error == error_data["error"]
    assert error_response.details == error_data["details"]