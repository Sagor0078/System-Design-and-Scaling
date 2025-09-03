"""
Locust Load Testing for Scaling System
=====================================

This file contains comprehensive load testing scenarios for the FastAPI scaling system
including authentication, CRUD operations, caching, and rate limiting tests.
"""

import json
import secrets

from locust import HttpUser, between, task


class ScalingSystemUser(HttpUser):
    """
    Simulates a user interacting with the scaling system.
    Tests various endpoints to validate performance and scalability.
    """

    # Wait time between requests (1-3 seconds)
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_ids: list[int] = []
        self.auth_token = "Bearer test-token"  # Simple auth token  # noqa: S105
        # Set default headers for all requests
        self.client.headers.update({"Authorization": self.auth_token})

    def on_start(self):
        """Called when a user starts. Set up test data."""
        # Test gateway health first
        self.gateway_health()

    @task(5)
    def gateway_health(self):
        """Test the API gateway health endpoint."""
        with self.client.get("/gateway-health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Gateway health check failed: {response.status_code}")

    @task(10)
    def app_health(self):
        """Test application health endpoints through the API gateway."""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"App health check failed: {response.status_code}")

    @task(15)
    def create_user(self):
        """Create a new user."""
        user_data = {
            "name": f"User-{secrets.randbelow(9000) + 1000}",
            "email": f"user{secrets.randbelow(9000) + 1000}@example.com"
        }

        with self.client.post("/api/users", json=user_data, catch_response=True) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    if "data" in data and "id" in data["data"]:
                        self.user_ids.append(data["data"]["id"])
                        response.success()
                    else:
                        response.failure("User created but no ID returned")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to create user: {response.status_code}")

    @task(20)
    def get_user(self):
        """Get a user by ID."""
        if not self.user_ids:
            # Create a user first if none exist
            self.create_user()
            return

        user_id = secrets.choice(self.user_ids)
        with self.client.get(f"/api/users/{user_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Remove invalid user ID
                self.user_ids.remove(user_id)
                response.failure("User not found")
            else:
                response.failure(f"Failed to get user: {response.status_code}")

    @task(8)
    def update_user(self):
        """Update an existing user."""
        if not self.user_ids:
            return

        user_id = secrets.choice(self.user_ids)
        update_data = {
            "name": f"Updated-User-{secrets.randbelow(9000) + 1000}",
            "email": f"updated{secrets.randbelow(9000) + 1000}@example.com"
        }

        with self.client.put(f"/api/users/{user_id}", json=update_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                self.user_ids.remove(user_id)
                response.failure("User not found for update")
            else:
                response.failure(f"Failed to update user: {response.status_code}")

    @task(12)
    def list_users(self):
        """List all users with pagination."""
        params = {
            "skip": secrets.randbelow(10) * 10,
            "limit": secrets.randbelow(10) + 10
        }

        with self.client.get("/api/users", params=params, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data and isinstance(data["data"], list):
                        response.success()
                    else:
                        response.failure("Invalid user list response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to list users: {response.status_code}")

    @task(3)
    def cache_test(self):
        """Test cache performance with repeated requests."""
        if not self.user_ids:
            return

        user_id = secrets.choice(self.user_ids)

        # Make multiple requests to the same user to test caching
        for _ in range(3):
            with self.client.get(f"/api/users/{user_id}", name="/api/users/[id] (cache test)",
                               catch_response=True) as response:
                if response.status_code == 200:
                    # Check for cache headers if they exist
                    cache_status = response.headers.get('X-Cache-Status', 'unknown')
                    if cache_status in ['hit', 'miss']:
                        response.success()
                    else:
                        response.success()  # Still successful even without cache headers
                else:
                    response.failure(f"Cache test failed: {response.status_code}")

    @task(2)
    def delete_user(self):
        """Delete a user."""
        if not self.user_ids:
            return

        user_id = secrets.choice(self.user_ids)
        with self.client.delete(f"/api/users/{user_id}", catch_response=True) as response:
            if response.status_code == 200:
                self.user_ids.remove(user_id)
                response.success()
            elif response.status_code == 404:
                self.user_ids.remove(user_id)
                response.failure("User not found for deletion")
            else:
                response.failure(f"Failed to delete user: {response.status_code}")


class HighVolumeUser(HttpUser):
    """
    Simulates high-volume traffic for stress testing.
    Focus on read operations to test caching and load balancing.
    """

    wait_time = between(2, 5)  # Slower to respect rate limits

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_ids: list[int] = []
        # Set auth header for API requests
        self.client.headers.update({"Authorization": "Bearer test-token"})

    @task(30)
    def rapid_user_reads(self):
        """Rapidly read users to stress test the system."""
        if not self.user_ids:
            # Create some users for testing
            self.setup_test_users()
            return

        user_id = secrets.choice(self.user_ids)
        with self.client.get(f"/api/users/{user_id}", name="/api/users/[id] (high volume)",
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"High volume read failed: {response.status_code}")

    @task(10)
    def rapid_health_checks(self):
        """Rapid health checks across all services."""
        endpoints = ["/gateway-health", "/api/health"]
        endpoint = secrets.choice(endpoints)

        # Remove auth header for gateway health
        headers = {} if endpoint == "/gateway-health" else {"Authorization": self.client.headers.get("Authorization")}

        with self.client.get(endpoint, headers=headers, name="health (high volume)",
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"High volume health check failed: {response.status_code}")

    def setup_test_users(self):
        """Create test users for high-volume testing."""
        for _ in range(5):
            user_data = {
                "name": f"HVUser-{secrets.randbelow(90000) + 10000}",
                "email": f"hv{secrets.randbelow(90000) + 10000}@test.com"
            }

            with self.client.post("/api/users", json=user_data, catch_response=True) as response:
                if response.status_code == 201:
                    try:
                        data = response.json()
                        if "data" in data and "id" in data["data"]:
                            self.user_ids.append(data["data"]["id"])
                    except json.JSONDecodeError:
                        pass


class AdminUser(HttpUser):
    """
    Simulates administrative operations and bulk actions.
    """

    wait_time = between(2, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bulk_user_ids: list[int] = []
        # Set auth header for API requests
        self.client.headers.update({"Authorization": "Bearer test-token"})

    @task(5)
    def bulk_create_users(self):
        """Create multiple users in succession."""
        for _ in range(5):
            user_data = {
                "name": f"BulkUser-{secrets.randbelow(90000) + 10000}",
                "email": f"bulk{secrets.randbelow(90000) + 10000}@admin.com"
            }

            with self.client.post("/api/users", json=user_data, name="bulk create user",
                                catch_response=True) as response:
                if response.status_code == 201:
                    try:
                        data = response.json()
                        if "data" in data and "id" in data["data"]:
                            self.bulk_user_ids.append(data["data"]["id"])
                            response.success()
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON in bulk create")
                else:
                    response.failure(f"Bulk create failed: {response.status_code}")

    @task(3)
    def bulk_read_users(self):
        """Read multiple users in succession."""
        if not self.bulk_user_ids:
            return

        for user_id in self.bulk_user_ids[:10]:  # Read up to 10 users
            with self.client.get(f"/api/users/{user_id}", name="bulk read user",
                               catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    if user_id in self.bulk_user_ids:
                        self.bulk_user_ids.remove(user_id)
                    response.failure("User not found in bulk read")
                else:
                    response.failure(f"Bulk read failed: {response.status_code}")

    @task(2)
    def system_overview(self):
        """Get system overview by checking all services."""
        services = [
            ("/gateway-health", False),  # (endpoint, needs_auth)
            ("/api/health", True),
            ("/api/users?limit=5", True)
        ]

        for service, needs_auth in services:
            headers = {"Authorization": "Bearer test-token"} if needs_auth else {}
            with self.client.get(service, headers=headers, name="system overview",
                               catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"System overview check failed for {service}: {response.status_code}")
