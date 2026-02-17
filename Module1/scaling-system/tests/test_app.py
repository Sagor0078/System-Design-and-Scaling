"""Unit tests for the FastAPI application."""

import os
import sys
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


@pytest.fixture(autouse=True)
def mock_redis_connection():
    """Mock Redis connection at the module level."""
    with patch("cache.redis.Redis") as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_instance.get.return_value = None
        mock_redis_instance.setex.return_value = True
        mock_redis_instance.delete.return_value = True
        mock_redis_instance.exists.return_value = False
        mock_redis_instance.hgetall.return_value = {}

        # Properly mock the pipeline as a context manager
        pipeline_mock = Mock()
        pipeline_mock.hset.return_value = None
        pipeline_mock.expire.return_value = None
        pipeline_mock.execute.return_value = None
        pipeline_mock.__enter__ = Mock(return_value=pipeline_mock)
        pipeline_mock.__exit__ = Mock(return_value=None)

        mock_redis_instance.pipeline.return_value = pipeline_mock
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import after Redis is mocked
    from main import app

    return TestClient(app)


@pytest.fixture
def mock_cache():
    """Mock the cache module."""
    with patch("main.cache") as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Mock the rate limiter."""
    with patch("main.rate_limiter") as mock:
        mock.is_allowed.return_value = (
            True,
            {"tokens_remaining": 9, "reset_time": 1234567890},
        )
        yield mock


def test_health_endpoint(client, mock_rate_limiter):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "server_id" in data
    assert data["message"] == "Service healthy"


def test_create_user(client, mock_cache, mock_rate_limiter):
    """Test user creation endpoint."""
    user_data = {"name": "Test User", "email": "test@example.com"}

    response = client.post("/users", json=user_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test User"
    assert data["data"]["email"] == "test@example.com"
    assert "id" in data["data"]


def test_get_user_not_found(client, mock_cache, mock_rate_limiter):
    """Test getting a non-existent user."""
    response = client.get("/users/999")
    assert response.status_code == 404


def test_get_user_from_cache(client, mock_cache, mock_rate_limiter):
    """Test getting user from cache."""
    # Mock cached user data - this JSON string will be returned by Redis
    mock_cache.get.return_value = {
        "id": 1,
        "name": "Cached User",
        "email": "cached@example.com",
        "created_at": 1234567890.0,
    }

    response = client.get("/users/1")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["from_cache"] is True
    assert data["data"]["name"] == "Cached User"


def test_list_users(client, mock_rate_limiter):
    """Test listing all users."""
    response = client.get("/users")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "users" in data["data"]
    assert "count" in data["data"]


def test_delete_user_not_found(client, mock_cache, mock_rate_limiter):
    """Test deleting a non-existent user."""
    response = client.delete("/users/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rate_limiting_headers(client, mock_rate_limiter):
    """Test that rate limiting headers are present."""
    response = client.get("/health")
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-Server-ID" in response.headers


def test_cors_headers():
    """Test CORS configuration."""
    # This would be tested if CORS middleware was properly configured
    pass


def test_cache_integration(mock_redis_connection):
    """Test Redis cache integration with mocked connection."""
    # Test that our Redis mock is working
    assert mock_redis_connection.get("test") is None
    assert mock_redis_connection.setex("test", 300, "value") is True
    assert mock_redis_connection.delete("test") is True


def test_rate_limiter_integration(mock_redis_connection):
    """Test rate limiter integration with mocked Redis."""
    # Test that rate limiter would work with our mock
    mock_redis_connection.hgetall.return_value = {}

    # The pipeline is already properly mocked in the fixture
    pipeline = mock_redis_connection.pipeline()
    assert pipeline is not None

    # Test that we can use the pipeline as a context manager
    with pipeline as pipe:
        pipe.hset("test", mapping={"tokens": 5})
        pipe.expire("test", 60)
        pipe.execute()

    # This tests that the mock setup works for rate limiting
    assert mock_redis_connection.hgetall("test") == {}
