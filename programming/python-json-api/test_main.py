import pytest
from fastapi.testclient import TestClient

import main
from main import app, items_db, users_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    items_db.clear()
    users_db.clear()
    main.next_id = 1
    main.next_user_id = 1


@pytest.fixture
def auth_headers():
    # Register and login a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    client.post("/register", json=user_data)

    login_data = {"username": "testuser", "password": "testpass123"}
    login_response = client.post("/login", json=login_data)
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Simple JSON API"}


def test_get_empty_items(auth_headers):
    response = client.get("/items", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_item(auth_headers):
    item_data = {"name": "Test Item", "description": "A test item", "price": 29.99}
    response = client.post("/items", json=item_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item"
    assert data["price"] == 29.99
    assert data["owner_id"] == 1


def test_create_item_without_description(auth_headers):
    item_data = {"name": "Test Item", "price": 29.99}
    response = client.post("/items", json=item_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Item"
    assert data["description"] is None
    assert data["price"] == 29.99
    assert data["owner_id"] == 1


def test_get_item_by_id(auth_headers):
    # First create an item
    item_data = {"name": "Test Item", "description": "A test item", "price": 29.99}
    client.post("/items", json=item_data, headers=auth_headers)

    # Then get it by ID
    response = client.get("/items/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Item"


def test_get_nonexistent_item(auth_headers):
    response = client.get("/items/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_get_all_items(auth_headers):
    # Create multiple items
    items_data = [
        {"name": "Item 1", "price": 10.0},
        {"name": "Item 2", "price": 20.0},
        {"name": "Item 3", "price": 30.0},
    ]

    for item in items_data:
        client.post("/items", json=item, headers=auth_headers)

    response = client.get("/items", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Item 1"
    assert data[1]["name"] == "Item 2"
    assert data[2]["name"] == "Item 3"


def test_update_item(auth_headers):
    # Create an item
    item_data = {
        "name": "Original Item",
        "description": "Original description",
        "price": 100.0,
    }
    client.post("/items", json=item_data, headers=auth_headers)

    # Update it
    updated_data = {
        "name": "Updated Item",
        "description": "Updated description",
        "price": 150.0,
    }
    response = client.put("/items/1", json=updated_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Updated Item"
    assert data["description"] == "Updated description"
    assert data["price"] == 150.0


def test_update_nonexistent_item(auth_headers):
    updated_data = {"name": "Updated Item", "price": 150.0}
    response = client.put("/items/999", json=updated_data, headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_delete_item(auth_headers):
    # Create an item
    item_data = {"name": "Item to Delete", "price": 50.0}
    client.post("/items", json=item_data, headers=auth_headers)

    # Delete it
    response = client.delete("/items/1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Item deleted successfully"}

    # Verify it's gone
    response = client.get("/items/1", headers=auth_headers)
    assert response.status_code == 404


def test_delete_nonexistent_item(auth_headers):
    response = client.delete("/items/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_invalid_item_data(auth_headers):
    # Test with missing required fields
    response = client.post("/items", json={"name": "Test"}, headers=auth_headers)
    assert response.status_code == 422  # Validation error

    # Test with invalid price type
    response = client.post(
        "/items", json={"name": "Test", "price": "not_a_number"}, headers=auth_headers
    )
    assert response.status_code == 422  # Validation error
