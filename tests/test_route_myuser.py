from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.database.models import User
from src.services.auth import auth_service


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


def test_read_myuser_me(client, token, user, monkeypatch):
    with patch.object(auth_service, "r") as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/myuser/me/",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == user["username"]
        assert data["email"] == user["email"]


def test_update_avatar_user(client, token, user, monkeypatch):
    USER_AVATAR = "http://cloudimage.com/image.png"
    with patch.object(auth_service, "r") as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
        monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        monkeypatch.setattr('src.services.cloud_image.CloudImage.generate_name_avatar', MagicMock())
        monkeypatch.setattr('src.services.cloud_image.CloudImage.upload', MagicMock())
        monkeypatch.setattr('src.services.cloud_image.CloudImage.get_url_for_avatar', MagicMock(return_value=USER_AVATAR))

        f = './fileupload.tst'
        with open(f, 'wb') as tmp:
            tmp.write(b'upload this')
        with open(f, 'rb') as tmp:
            response = client.patch("/api/myuser/avatar",
                                    files={"file": ("filename", tmp, "image/jpeg")},
                                    # files=files,
                                    headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["username"] == user["username"]
            assert data["email"] == user["email"]
            assert data["avatar"] == USER_AVATAR
