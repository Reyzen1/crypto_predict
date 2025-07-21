# tests/test_basic_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_info_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data

def test_crypto_list_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/crypto/")
    assert response.status_code == 200

def test_tasks_safe_status():
    client = TestClient(app)
    response = client.get("/api/v1/tasks-safe/status")
    assert response.status_code == 200
