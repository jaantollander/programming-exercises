from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import app, items_db, oidc_config, users_db
from oidc_config import OIDCProvider

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    users_db.clear()
    items_db.clear()
    main.next_user_id = 1
    main.next_id = 1
    oidc_config.providers.clear()
    oidc_config.jwks_cache.clear()
    oidc_config.jwks_cache_expiry.clear()


@pytest.fixture
def mock_jwks():
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }


@pytest.fixture
def oidc_test_provider():
    provider = OIDCProvider(
        name="test-provider",
        issuer="https://test-issuer.com",
        client_id="test-client-id",
        algorithms=["RS256"],
    )
    oidc_config.add_provider(provider)
    return provider


def test_oidc_config_disabled():
    """Test OIDC config endpoint when OIDC is disabled"""
    with patch("main.OIDC_ENABLED", False):
        response = client.get("/auth/oidc/config")
        assert response.status_code == 200
        data = response.json()
        assert data["oidc_enabled"] == False


def test_oidc_config_enabled(oidc_test_provider):
    """Test OIDC config endpoint when OIDC is enabled"""
    with patch("main.OIDC_ENABLED", True):
        response = client.get("/auth/oidc/config")
        assert response.status_code == 200
        data = response.json()
        assert data["oidc_enabled"] == True
        assert "providers" in data
        assert "test-provider" in data["providers"]
        assert data["providers"]["test-provider"]["issuer"] == "https://test-issuer.com"


@patch("requests.get")
def test_jwks_discovery(mock_get, oidc_test_provider, mock_jwks):
    """Test JWKS discovery from well-known endpoint"""
    # Mock well-known config response
    mock_config_response = MagicMock()
    mock_config_response.json.return_value = {
        "jwks_uri": "https://test-issuer.com/.well-known/jwks.json"
    }
    mock_config_response.raise_for_status.return_value = None

    # Mock JWKS response
    mock_jwks_response = MagicMock()
    mock_jwks_response.json.return_value = mock_jwks
    mock_jwks_response.raise_for_status.return_value = None

    mock_get.side_effect = [mock_config_response, mock_jwks_response]

    # Trigger discovery
    oidc_config._discover_jwks("test-provider", "https://test-issuer.com")

    # Verify JWKS was cached
    assert "test-provider" in oidc_config.jwks_cache
    assert oidc_config.jwks_cache["test-provider"] == mock_jwks


@patch("main.oidc_config.validate_token")
def test_oidc_token_authentication(mock_validate, oidc_test_provider):
    """Test authentication with OIDC token"""
    # Mock OIDC payload
    oidc_payload = {
        "sub": "oidc-user-123",
        "iss": "https://test-issuer.com",
        "email": "oidc.user@example.com",
        "name": "OIDC User",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    }

    mock_validate.return_value = oidc_payload

    with patch("main.OIDC_ENABLED", True):
        # Test creating item with OIDC token
        headers = {"Authorization": "Bearer fake-oidc-token"}
        item_data = {"name": "OIDC Item", "price": 100.0}

        response = client.post("/items", json=item_data, headers=headers)
        assert response.status_code == 200

        # Verify user was created
        assert len(users_db) == 1
        user = users_db[0]
        assert user.username == "OIDC User"
        assert user.email == "oidc.user@example.com"
        assert user.oidc_subject == "oidc-user-123"
        assert user.oidc_provider == "test-provider"


def test_oidc_user_info_endpoint():
    """Test getting user info for OIDC user"""
    # Create OIDC user manually
    oidc_user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "OIDC User",
            "email": "oidc@example.com",
            "oidc_subject": "oidc-123",
            "oidc_provider": "test-provider",
        },
    )()

    # Override the get_current_user dependency
    def mock_get_current_user():
        return oidc_user

    app.dependency_overrides[main.get_current_user] = mock_get_current_user

    try:
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["auth_type"] == "oidc"
        assert data["oidc_provider"] == "test-provider"
        assert data["username"] == "OIDC User"
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_local_user_info_endpoint():
    """Test getting user info for local user"""
    # Create local user
    local_user = type(
        "User", (), {"id": 1, "username": "Local User", "email": "local@example.com"}
    )()

    # Override the get_current_user dependency
    def mock_get_current_user():
        return local_user

    app.dependency_overrides[main.get_current_user] = mock_get_current_user

    try:
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["auth_type"] == "local"
        assert "oidc_provider" not in data
        assert data["username"] == "Local User"
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


@patch("main.oidc_config.validate_token")
def test_oidc_existing_user_login(mock_validate, oidc_test_provider):
    """Test that existing OIDC user is found on subsequent logins"""
    # Create existing OIDC user
    existing_user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "Existing OIDC User",
            "email": "existing@example.com",
            "oidc_subject": "existing-123",
            "oidc_provider": "test-provider",
        },
    )()
    users_db.append(existing_user)
    main.next_user_id = 2

    # Mock OIDC payload for same user
    oidc_payload = {
        "sub": "existing-123",
        "iss": "https://test-issuer.com",
        "email": "existing@example.com",
        "name": "Existing OIDC User",
    }

    mock_validate.return_value = oidc_payload

    with patch("main.OIDC_ENABLED", True):
        headers = {"Authorization": "Bearer fake-oidc-token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200

        # Should still be only 1 user (no duplicate created)
        assert len(users_db) == 1
        assert users_db[0].id == 1


def test_fallback_to_local_jwt():
    """Test that local JWT still works when OIDC is enabled"""
    # Create local user
    user_data = {
        "username": "localuser",
        "email": "local@example.com",
        "password": "testpass123",
    }

    # Register and login with local auth
    client.post("/register", json=user_data)
    login_response = client.post(
        "/login", json={"username": "localuser", "password": "testpass123"}
    )

    token = login_response.json()["access_token"]

    with patch("main.OIDC_ENABLED", True):
        with patch("main.oidc_config.validate_token", return_value=None):
            # Should fall back to local JWT validation
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["auth_type"] == "local"
            assert data["username"] == "localuser"


@patch("main.oidc_config.validate_token")
def test_invalid_oidc_token(mock_validate):
    """Test handling of invalid OIDC token"""
    mock_validate.return_value = None  # Invalid token

    with patch("main.OIDC_ENABLED", True):
        headers = {"Authorization": "Bearer invalid-oidc-token"}
        response = client.get("/auth/me", headers=headers)
        # Should fail since token is invalid and no local fallback
        assert response.status_code == 401
