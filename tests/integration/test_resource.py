import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile
from io import BytesIO
from app.operations.resource import create_resource, update_resource_file
from app.models.resource import Resource, ResourceType
from app.utils.minio_client import minio_client, BUCKET_NAME

@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database transactions."""
    session = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_user():
    """Mock user object."""
    return MagicMock(id=str(uuid.uuid4()))

@pytest.fixture
def mock_upload_file():
    """Mock an UploadFile object."""
    file_data = b"test file content"
    file = BytesIO(file_data)
    return UploadFile(filename="test.pdf", file=file)

@pytest.fixture
def mock_resource(mock_user):
    """Mock a Resource object."""
    return Resource(
        id=str(uuid.uuid4()),
        user_id=mock_user.id,
        resource_type=ResourceType.PDF,
        name="Test Resource",
        description="A test resource",
        file_path="mock/path/to/file.pdf",
        external_url="http://mock-url.com/file.pdf"
    )

@pytest.mark.asyncio
async def test_create_resource(mock_db_session, mock_upload_file, mock_user):
    """Test uploading a resource and storing metadata."""
    minio_client.put_object = MagicMock()
    minio_client.presigned_get_object = MagicMock(return_value="http://mock-url.com/test")

    resource = await create_resource(
        db=mock_db_session,
        file=mock_upload_file,
        name="Test File",
        description="This is a test file",
        user=mock_user,
        category="documents",
        tags="test, example"
    )

    assert resource is not None
    assert resource.name == "Test File"
    assert resource.description == "This is a test file"
    assert resource.category == "documents"
    assert resource.tags == "test, example"
    assert "mock-url.com" in resource.external_url
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_resource_file(mock_db_session, mock_resource, mock_upload_file):
    """Test updating a resource file."""
    minio_client.put_object = MagicMock()
    minio_client.presigned_get_object = MagicMock(return_value="http://mock-url.com/updated")

    updated_file_path = await update_resource_file(
        db=mock_db_session,
        resource=mock_resource,
        file=mock_upload_file
    )

    assert "mock-url.com" in mock_resource.external_url
    mock_db_session.commit.assert_called_once()