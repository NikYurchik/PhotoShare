from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.database.models import User
from src.services.auth import auth_service
from src.services.roles import Role
from src.conf import messages


USER2 = {"username": "test1",
         "email": "test1@example.com",
         "password": "123456789",
         "roles": "user",
         "is_banned": "False"
        }


@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    current_user.roles = Role.admin
    session.commit()
    
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    access_token = data["access_token"]
    
    client.post("/api/auth/signup", json=USER2)
    current_user2: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user2.confirmed = True
    session.commit()

    return access_token


def test_set_roles_user(client, token, user, monkeypatch):
    # with patch.object(auth_service, 'r') as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.patch(
            "/api/users/set_roles/2/?user_roles=moderator",
            json=USER2,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == USER2["username"]
        assert data["email"] == USER2["email"]
        assert data["roles"] != USER2["roles"]


def test_set_roles_user_notfound(client, token, user, monkeypatch):
    # with patch.object(auth_service, 'r') as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.patch(
            "/api/users/set_roles/999/?user_roles=moderator",
            json=user,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == messages.NOT_FOUND


def test_set_roles_user_forbidden(client, token, user, monkeypatch):
    # with patch.object(auth_service, 'r') as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.patch(
            "/api/users/set_roles/1/?user_roles=moderator",
            json=user,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, response.text
        data = response.json()
        assert data["detail"] == messages.FORBIDDEN

