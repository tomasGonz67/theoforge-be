import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_guest(async_client: AsyncClient):
    """Integration test for creating a guest via API."""
    guest_data = {
        "session_id": "integration_test_session",
        "page_views": ["/integration", "/test"],
        "interaction_events": ["clicked_integration_test"],
        "status": "NEW",
        "interaction_history": [{"event": "integration_test", "timestamp": "2025-03-01T12:00:00Z"}],
    }

    response = await async_client.post("/guests/", json=guest_data)
    assert response.status_code == 200
    assert response.json()["session_id"] == "integration_test_session"
