from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.database.models import User
from src.services.auth import auth_service
from src.services.roles import Role
from src.conf import messages


@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]


def test_get_users_forbidden(client, token, user, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/users",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403, response.text
        data = response.json()
        assert data["detail"] == messages.FORBIDDEN


def test_get_users(client, token, user, session, monkeypatch):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.roles = Role.admin
    session.commit()
    
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())
    if True:
        response = client.get("/api/users",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert type(data) == list
        assert data[0]["username"] == user["username"]
        assert data[0]["email"] == user["email"]


def test_get_users_mask(client, token, user, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/users/?search_mask=%oo%",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert type(data) == list
        assert data[0]["username"] == user["username"]
        assert data[0]["email"] == user["email"]


def test_get_users_mask_notfound(client, token, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/users/?search_mask=%fff%",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert type(data) == list
        assert len(data) == 0


def test_get_user_id(client, token, user, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/users/1",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == user["username"]
        assert data["email"] == user["email"]


def test_get_user_id_notfound(client, token, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/users/999",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == messages.NOT_FOUND


