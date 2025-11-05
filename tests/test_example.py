"""
Example tests for MCP server
"""

import pytest
from fastapi.testclient import TestClient

from app.core.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_discover_tools(client):
    """Test tool discovery endpoint"""
    response = client.get("/tools/discover")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "server_info" in data
    assert isinstance(data["tools"], list)


def test_list_tools(client):
    """Test simplified tools list endpoint"""
    response = client.get("/tools/list")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "count" in data
    assert isinstance(data["tools"], list)


@pytest.mark.asyncio
async def test_example_tool_execution(client):
    """Test example tool execution"""
    response = client.post(
        "/tools/example_tool",
        json={
            "arguments": {
                "input_text": "Hello World",
                "uppercase": True,
            },
            "context": {"user_id": "test_user"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "result" in data["data"]
    assert "HELLO WORLD" in data["data"]["result"]
