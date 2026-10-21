from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint_is_registered():
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/v1/auth/login" in paths
