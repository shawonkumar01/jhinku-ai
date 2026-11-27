
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import JWT_ALGORITHM, SECRET_KEY


def register(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
        },
    )


def login(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["is_active"] is True
    # Password hash must never be exposed.
    assert "password_hash" not in body
    assert "password" not in body


def test_register_duplicate_email(client):
    assert register(client).status_code == 201
    response = register(client)
    assert response.status_code == 409


def test_register_invalid_email(client):
    response = register(client, email="not-an-email")
    assert response.status_code == 422


def test_register_short_password(client):
    response = register(client, password="short")
    assert response.status_code == 422


def test_login_success(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    register(client)
    response = login(client, password="wrongpassword")
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = login(client, email="nobody@example.com")
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token(client):
    register(client)
    tokens = login(client).json()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_me_with_expired_access_token(client):
    register(client)
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401


def test_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer garbage"},
    )
    assert response.status_code == 401


def test_refresh_rotates_token(client):
    register(client)
    tokens = login(client).json()
    old_refresh = tokens["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != old_refresh

    # The old refresh token must now be revoked.
    reuse = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert reuse.status_code == 401


def test_refresh_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
    )
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    register(client)
    tokens = login(client).json()
    refresh = tokens["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh}
    )
    assert response.status_code == 204

    reuse = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert reuse.status_code == 401
