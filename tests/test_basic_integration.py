# File: tests/test_basic_integration.py
# Basic integration tests for CryptoPredict API - CLEAN VERSION

import pytest
from fastapi.testclient import TestClient

# Clean imports - no sys.path manipulation needed


def test_health_endpoint(client):
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_api_info_endpoint(client):
    """Test the API info endpoint"""  
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "CryptoPredict MVP API"


def test_crypto_list_endpoint(client):
    """Test cryptocurrency list endpoint (should return empty list)"""
    response = client.get("/api/v1/crypto/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Empty list is expected for tests since database is fresh


def test_tasks_safe_status(client):
    """Test safe tasks status endpoint"""
    response = client.get("/api/v1/tasks/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_system_health_endpoint(client):
    """Test system health endpoint"""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_system_database_endpoint(client):
    """Test system database endpoint"""
    response = client.get("/api/v1/system/database")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200


def test_api_v1_health_endpoint(client):
    """Test API v1 health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data