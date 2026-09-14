import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.core.supabase_client import get_supabase
from app.dependencies import get_current_user

mock_supabase = MagicMock()

def override_get_supabase():
    return mock_supabase

@pytest.fixture(autouse=True)
def setup_overrides():
    old_supabase = app.dependency_overrides.get(get_supabase)
    app.dependency_overrides[get_supabase] = override_get_supabase
    
    yield
    
    if old_supabase:
        app.dependency_overrides[get_supabase] = old_supabase
    else:
        del app.dependency_overrides[get_supabase]

client = TestClient(app)

def test_unauthenticated_request_current():
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
        
    response = client.get("/risk/test-user-id/current")
    assert response.status_code == 401

def test_unauthenticated_request_history():
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
        
    response = client.get("/risk/test-user-id/history")
    assert response.status_code == 401

def test_get_current_not_found():
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user-id"}
    
    # Mock empty data
    mock_supabase.table().select().eq().order().limit().execute.return_value.data = []
    
    response = client.get("/risk/test-user-id/current")
    assert response.status_code == 404
    assert response.json()["detail"] == "No risk score found for user"

def test_get_history_empty_list():
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user-id"}
    
    # Mock empty data
    mock_supabase.table().select().eq().order().execute.return_value.data = []
    
    response = client.get("/risk/test-user-id/history")
    assert response.status_code == 200
    assert response.json() == {"scores": []}
