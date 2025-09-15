import pytest
from fastapi.testclient import TestClient

import main
from main import app, items_db, users_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    users_db.clear()
    items_db.clear()
    main.next_user_id = 1
    main.next_id = 1


@pytest.fixture
def test_user():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    response = client.post("/register", json=user_data)
    return response.json(), user_data["password"]


@pytest.fixture
def auth_token(test_user):
    user, password = test_user
    login_data = {"username": user["username"], "password": password}
    response = client.post("/login", json=login_data)
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def test_register_user():
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpass123",
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "password" not in data
    assert "id" in data


def test_register_duplicate_user(test_user):
    user, _ = test_user
    user_data = {
        "username": user["username"],
        "email": "different@example.com",
        "password": "differentpass",
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_valid_user(test_user):
    user, password = test_user
    login_data = {"username": user["username"], "password": password}
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


def test_login_invalid_user():
    login_data = {"username": "nonexistent", "password": "wrongpass"}
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_wrong_password(test_user):
    user, _ = test_user
    login_data = {"username": user["username"], "password": "wrongpassword"}
    response = client.post("/login", json=login_data)
    assert response.status_code == 401


def test_create_item_authenticated(auth_headers):
    item_data = {
        "name": "Authenticated Item",
        "description": "This requires auth",
        "price": 99.99,
    }
    response = client.post("/items", json=item_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Authenticated Item"
    assert data["owner_id"] == 1


def test_create_item_unauthenticated():
    item_data = {"name": "Unauthenticated Item", "price": 50.0}
    response = client.post("/items", json=item_data)
    assert response.status_code == 403


def test_create_item_invalid_token():
    item_data = {"name": "Invalid Token Item", "price": 50.0}
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/items", json=item_data, headers=headers)
    assert response.status_code == 401


def test_get_items_no_auth():
    # Reading items now requires auth
    response = client.get("/items")
    assert response.status_code == 403


def test_get_specific_item_no_auth(auth_headers):
    # Create an item first
    item_data = {"name": "Private Item", "price": 25.0}
    create_response = client.post("/items", json=item_data, headers=auth_headers)
    item_id = create_response.json()["id"]

    # Should NOT be able to read it without auth
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 403


def test_update_own_item(auth_headers):
    # Create an item
    item_data = {"name": "Original", "price": 100.0}
    create_response = client.post("/items", json=item_data, headers=auth_headers)
    item_id = create_response.json()["id"]

    # Update it
    update_data = {"name": "Updated", "price": 150.0}
    response = client.put(f"/items/{item_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_update_item_unauthenticated():
    update_data = {"name": "Unauthorized Update", "price": 200.0}
    response = client.put("/items/1", json=update_data)
    assert response.status_code == 403


def test_update_others_item(auth_headers):
    # Create user 1 and their item
    item_data = {"name": "User1 Item", "price": 100.0}
    create_response = client.post("/items", json=item_data, headers=auth_headers)
    item_id = create_response.json()["id"]

    # Create user 2
    user2_data = {
        "username": "user2",
        "email": "user2@example.com",
        "password": "pass2",
    }
    client.post("/register", json=user2_data)

    # Login as user 2
    login_response = client.post(
        "/login", json={"username": "user2", "password": "pass2"}
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Try to update user1's item as user2
    update_data = {"name": "Unauthorized Update", "price": 200.0}
    response = client.put(f"/items/{item_id}", json=update_data, headers=user2_headers)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_delete_own_item(auth_headers):
    # Create an item
    item_data = {"name": "To Delete", "price": 50.0}
    create_response = client.post("/items", json=item_data, headers=auth_headers)
    item_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/items/{item_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_delete_item_unauthenticated():
    response = client.delete("/items/1")
    assert response.status_code == 403


def test_delete_others_item(auth_headers):
    # Create user 1 and their item
    item_data = {"name": "User1 Item", "price": 100.0}
    create_response = client.post("/items", json=item_data, headers=auth_headers)
    item_id = create_response.json()["id"]

    # Create user 2
    user2_data = {
        "username": "user2delete",
        "email": "user2delete@example.com",
        "password": "pass2delete",
    }
    client.post("/register", json=user2_data)

    # Login as user 2
    login_response = client.post(
        "/login", json={"username": "user2delete", "password": "pass2delete"}
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Try to delete user1's item as user2
    response = client.delete(f"/items/{item_id}", headers=user2_headers)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_users_only_see_own_items(auth_headers):
    # User 1 creates items
    user1_items = [
        {"name": "User1 Item1", "price": 10.0},
        {"name": "User1 Item2", "price": 20.0},
    ]
    for item in user1_items:
        client.post("/items", json=item, headers=auth_headers)

    # Create user 2
    user2_data = {
        "username": "user2items",
        "email": "user2items@example.com",
        "password": "pass2items",
    }
    client.post("/register", json=user2_data)

    # Login as user 2
    login_response = client.post(
        "/login", json={"username": "user2items", "password": "pass2items"}
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User 2 creates items
    user2_items = [
        {"name": "User2 Item1", "price": 30.0},
        {"name": "User2 Item2", "price": 40.0},
    ]
    for item in user2_items:
        client.post("/items", json=item, headers=user2_headers)

    # User 1 should only see their own items
    user1_response = client.get("/items", headers=auth_headers)
    user1_data = user1_response.json()
    assert len(user1_data) == 2
    assert all(item["owner_id"] == 1 for item in user1_data)
    assert user1_data[0]["name"] == "User1 Item1"
    assert user1_data[1]["name"] == "User1 Item2"

    # User 2 should only see their own items
    user2_response = client.get("/items", headers=user2_headers)
    user2_data = user2_response.json()
    assert len(user2_data) == 2
    assert all(item["owner_id"] == 2 for item in user2_data)
    assert user2_data[0]["name"] == "User2 Item1"
    assert user2_data[1]["name"] == "User2 Item2"
