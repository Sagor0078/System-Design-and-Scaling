import time
from concurrent.futures import ThreadPoolExecutor

import requests

BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"Authorization": "Bearer dummy-token"}


def test_health():
    """Test health endpoints"""
    print("=== Health Check Tests ===")

    # Gateway health
    response = requests.get(f"{BASE_URL}/gateway-health")
    print(f"Gateway Health: {response.status_code} - {response.text.strip()}")

    # App health through API
    response = requests.get(f"{BASE_URL}/api/health", headers=AUTH_HEADER)
    if response.status_code == 200:
        data = response.json()
        print(f"App Health: {data['message']} - Server: {data['server_id']}")


def test_load_balancing():
    """Test load balancing by making multiple requests"""
    print("\n=== Load Balancing Test ===")

    servers_hit = set()
    for i in range(10):
        response = requests.get(f"{BASE_URL}/api/health", headers=AUTH_HEADER)
        if response.status_code == 200:
            server_id = response.json().get("server_id")
            servers_hit.add(server_id)
            print(f"Request {i + 1}: Server {server_id}")
        time.sleep(0.1)

    print(f"Hit {len(servers_hit)} different servers: {servers_hit}")


def test_caching():
    """Test Redis caching"""
    print("\n=== Caching Test ===")

    # Create a user
    user_data = {"name": "Test User", "email": "test@example.com"}
    response = requests.post(
        f"{BASE_URL}/api/users", json=user_data, headers=AUTH_HEADER
    )
    user_id = response.json()["data"]["id"]
    print(f"Created user with ID: {user_id}")

    # First get (from database)
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=AUTH_HEADER)
    db_time = time.time() - start_time
    db_response = response.json()
    print(
        f"DB Response ({db_time:.3f}s): from_cache={db_response['data']['from_cache']}"
    )

    # Second get (from cache)
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=AUTH_HEADER)
    cache_time = time.time() - start_time
    cache_response = response.json()
    print(
        f"Cache Response ({cache_time:.3f}s): from_cache={cache_response['data']['from_cache']}"
    )


def test_rate_limiting():
    """Test rate limiting"""
    print("\n=== Rate Limiting Test ===")

    def make_request(i):
        try:
            response = requests.get(f"{BASE_URL}/api/health", headers=AUTH_HEADER)
            return f"Request {i}: {response.status_code}"
        except Exception as e:
            return f"Request {i}: Error - {e}"

    # Make rapid requests to trigger rate limiting
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = [future.result() for future in futures]

    for result in results[:15]:  # Show first 15 results
        print(result)


def test_crud_operations():
    """Test CRUD operations"""
    print("\n=== CRUD Operations Test ===")

    # Create users
    users = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]

    created_ids = []
    for user in users:
        response = requests.post(
            f"{BASE_URL}/api/users", json=user, headers=AUTH_HEADER
        )
        user_id = response.json()["data"]["id"]
        created_ids.append(user_id)
        print(f"Created user: {user['name']} (ID: {user_id})")

    # List users
    response = requests.get(f"{BASE_URL}/api/users", headers=AUTH_HEADER)
    user_count = response.json()["data"]["count"]
    print(f"Total users: {user_count}")

    # Delete one user
    if created_ids:
        user_id = created_ids[0]
        response = requests.delete(
            f"{BASE_URL}/api/users/{user_id}", headers=AUTH_HEADER
        )
        print(f"Deleted user ID: {user_id}")


if __name__ == "__main__":
    print("Testing Scalable System...")
    print("Make sure the system is running: docker-compose up -d")
    time.sleep(2)

    try:
        test_health()
        test_load_balancing()
        test_caching()
        test_crud_operations()
        test_rate_limiting()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the system. Make sure it's running.")
    except Exception as e:
        print(f"Test error: {e}")
