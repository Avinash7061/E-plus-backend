import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.core.supabase_client import get_supabase

mock_supabase = MagicMock()

def override_get_supabase():
    return mock_supabase

@pytest.fixture(autouse=True)
def setup_overrides():
    old = app.dependency_overrides.get(get_supabase)
    app.dependency_overrides[get_supabase] = override_get_supabase
    yield
    if old:
        app.dependency_overrides[get_supabase] = old
    else:
        del app.dependency_overrides[get_supabase]

client = TestClient(app)

def test_register_success():
    """Tests successful user registration"""
    mock_supabase.table().select().eq().execute.return_value.data = []
    mock_supabase.table().insert().execute.return_value.data = [
        {"id": "uuid-1234", "phone_number": "1234567890", "full_name": "Test User", "role": "patient", "created_at": "2023-01-01T00:00:00Z"}
    ]
    
    response = client.post("/auth/register", json={"phone_number": "1234567890", "full_name": "Test User"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["user"]["phone_number"] == "1234567890"

def test_register_duplicate_phone():
    """Tests that registering an existing phone number returns 400"""
    mock_supabase.table().select().eq().execute.return_value.data = [{"id": "uuid-1234"}]
    
    response = client.post("/auth/register", json={"phone_number": "1234567890"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Phone number already registered"

def test_login_not_found():
    """Tests that logging in with an unknown phone number returns 404"""
    mock_supabase.table().select().eq().execute.return_value.data = []
    
    response = client.post("/auth/login", json={"phone_number": "0000000000"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
