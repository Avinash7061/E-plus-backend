"""Router tests for /alerts endpoints — Supabase mocked via FastAPI dependency_overrides."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase_client import get_supabase
from app.dependencies import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_supabase, None)

def _auth_headers():
    return {"Authorization": "Bearer faketoken"}


def test_list_alerts_unauthenticated():
    response = client.get("/alerts/some-user-id")
    assert response.status_code == 401


def test_acknowledge_unauthenticated():
    response = client.post("/alerts/some-alert-id/acknowledge")
    assert response.status_code == 401


def test_acknowledge_not_found():
    mock_db = MagicMock()
    mock_db.table().select().eq().execute.return_value.data = []

    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-1", "phone_number": "1234567890", "role": "patient"
    }
    app.dependency_overrides[get_supabase] = lambda: mock_db

    response = client.post("/alerts/nonexistent-id/acknowledge", headers=_auth_headers())
    assert response.status_code == 404


def test_acknowledge_success():
    mock_db = MagicMock()
    mock_db.table().select().eq().execute.return_value.data = [
        {"id": "alert-1", "user_id": "user-1", "acknowledged": False}
    ]
    mock_db.table().update().eq().execute.return_value.data = [
        {
            "id": "alert-1",
            "user_id": "user-1",
            "acknowledged": True,
            "channel": "sms",
            "message": "test",
            "sent_at": "2026-01-01T00:00:00Z",
        }
    ]

    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-1", "phone_number": "1234567890", "role": "patient"
    }
    app.dependency_overrides[get_supabase] = lambda: mock_db

    response = client.post("/alerts/alert-1/acknowledge", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True