"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "DeepROS Platform API"
    assert data["version"] == "0.1.0"


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_domain(client: TestClient):
    """Test creating a ROS domain."""
    domain_data = {
        "name": "test_domain",
        "description": "Test domain for testing",
        "agent_status": "active"
    }
    response = client.post("/api/v1/domains/", json=domain_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == domain_data["name"]
    assert data["description"] == domain_data["description"]
    assert data["agent_status"] == domain_data["agent_status"]
    assert "id" in data


def test_create_node(client: TestClient):
    """Test creating a node."""
    # First create a domain
    domain_data = {"name": "test_domain", "description": "Test domain"}
    domain_response = client.post("/api/v1/domains/", json=domain_data)
    domain_id = domain_response.json()["id"]
    
    # Create a node
    node_data = {
        "name": "test_node",
        "domain_id": domain_id,
        "node_type": "topic",
        "status": "active",
        "metadata": {"frequency": 10}
    }
    response = client.post("/api/v1/nodes/", json=node_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == node_data["name"]
    assert data["domain_id"] == domain_id
    assert data["node_type"] == node_data["node_type"]


def test_get_domains(client: TestClient):
    """Test getting domains."""
    response = client.get("/api/v1/domains/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_nodes(client: TestClient):
    """Test getting nodes."""
    response = client.get("/api/v1/nodes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 