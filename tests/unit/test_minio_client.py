import os
import io
from unittest import mock
import pytest
from minio import Minio

# We need to patch the module before importing it to capture the initialization
with mock.patch('minio.Minio'):
    from app.utils.minio_client import BUCKET_NAME


@pytest.fixture
def mock_minio_client():
    """Fixture to mock the MinIO client and control its behavior in tests."""
    with mock.patch('minio.Minio', autospec=True) as mock_minio_class:
        # Create our mock instance that will be returned when Minio is instantiated
        mock_instance = mock.MagicMock()
        mock_minio_class.return_value = mock_instance
        
        # When the module is imported, it will use our mock_instance
        with mock.patch('app.utils.minio_client.minio_client', mock_instance):
            yield mock_instance


@pytest.fixture
def mock_environment():
    """Fixture to control environment variables for tests."""
    # Save original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "MINIO_ENDPOINT": "http://test-minio:9000",
        "MINIO_ACCESS_KEY": "test-access-key",
        "MINIO_SECRET_KEY": "test-secret-key",
        "MINIO_BUCKET_NAME": "test-bucket"
    }
    
    # Update environment with test values
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def test_minio_client_initialization():
    """Test that the MinIO client is initialized with correct parameters."""
    with mock.patch('minio.Minio', autospec=True) as mock_minio_class:
        # Force module reload with our mock
        with mock.patch.dict('os.environ', {
            "MINIO_ENDPOINT": "http://minio:9000",
            "MINIO_ACCESS_KEY": "minioadmin",
            "MINIO_SECRET_KEY": "minioadmin",
            "MINIO_BUCKET_NAME": "resources"
        }):
            # Force reimport to trigger initialization code
            import importlib
            import app.utils.minio_client
            importlib.reload(app.utils.minio_client)
        
        # Check that Minio was initialized with the expected parameters
        mock_minio_class.assert_called_once()
        args, kwargs = mock_minio_class.call_args
        assert kwargs['access_key'] == 'minioadmin'
        assert kwargs['secret_key'] == 'minioadmin'
        assert kwargs['secure'] is False
        assert args[0] == 'minio:9000'


def test_minio_client_initialization_with_env_vars(mock_environment):
    """Test that the MinIO client uses environment variables when available."""
    with mock.patch('minio.Minio', autospec=True) as mock_minio_class:
        # Force reimport to trigger initialization code with our environment vars
        import importlib
        import app.utils.minio_client
        importlib.reload(app.utils.minio_client)
        
        # Check that Minio was initialized with the parameters from environment
        mock_minio_class.assert_called_once()
        args, kwargs = mock_minio_class.call_args
        assert kwargs['access_key'] == 'test-access-key'
        assert kwargs['secret_key'] == 'test-secret-key'
        assert kwargs['secure'] is False
        assert args[0] == 'test-minio:9000'


def test_bucket_exists_true():
    """Test the case when the bucket already exists."""
    with mock.patch('minio.Minio') as mock_minio_class:
        # Configure mock instance
        mock_instance = mock.MagicMock()
        mock_minio_class.return_value = mock_instance
        mock_instance.bucket_exists.return_value = True
        
        # Capture print statements
        with mock.patch('builtins.print') as mock_print:
            # Import module to trigger initialization and bucket check
            import importlib
            import app.utils.minio_client
            importlib.reload(app.utils.minio_client)
            
            # Verify bucket_exists was called
            mock_instance.bucket_exists.assert_called_once()
            
            # Verify make_bucket was not called
            mock_instance.make_bucket.assert_not_called()
            
            # Verify the correct message was printed
            expected_bucket = os.environ.get("MINIO_BUCKET_NAME", "resources")
            mock_print.assert_called_with(f"Bucket '{expected_bucket}' already exists.")


def test_bucket_exists_false():
    """Test the case when the bucket does not exist and needs to be created."""
    with mock.patch('minio.Minio') as mock_minio_class:
        # Configure mock instance
        mock_instance = mock.MagicMock()
        mock_minio_class.return_value = mock_instance
        mock_instance.bucket_exists.return_value = False
        
        # Capture print statements
        with mock.patch('builtins.print') as mock_print:
            # Import module to trigger initialization and bucket check
            import importlib
            import app.utils.minio_client
            importlib.reload(app.utils.minio_client)
            
            # Verify bucket_exists was called
            mock_instance.bucket_exists.assert_called_once()
            
            # Verify make_bucket was called
            mock_instance.make_bucket.assert_called_once()
            
            # Verify the correct message was printed
            expected_bucket = os.environ.get("MINIO_BUCKET_NAME", "resources")
            mock_print.assert_called_with(f"Bucket '{expected_bucket}' created successfully.")


@pytest.mark.parametrize("file_data", [
    b"test file content",
    b"another test content",
])
def test_file_operations(mock_minio_client, file_data):
    """Test file upload and download operations with MinIO client."""
    # Set up test parameters
    bucket_name = os.environ.get("MINIO_BUCKET_NAME", "resources")
    object_name = "test_file.txt"
    content_type = "text/plain"
    
    # Test file upload
    data = io.BytesIO(file_data)
    data_size = len(file_data)
    
    # Call the MinIO client to put an object (upload a file)
    mock_minio_client.put_object(
        bucket_name, object_name, data, data_size, content_type=content_type
    )
    
    # Verify put_object was called with expected parameters
    mock_minio_client.put_object.assert_called_once()
    call_args = mock_minio_client.put_object.call_args[0]
    assert call_args[0] == bucket_name
    assert call_args[1] == object_name
    assert call_args[3] == data_size
    
    # Test file download - setup the response
    mock_response = mock.MagicMock()
    mock_response.data = file_data
    mock_minio_client.get_object.return_value = mock_response
    
    # Get the object
    response = mock_minio_client.get_object(bucket_name, object_name)
    
    # Verify get_object was called with expected parameters
    mock_minio_client.get_object.assert_called_once_with(bucket_name, object_name)
    
    # Verify the response contains the expected data
    assert response.data == file_data