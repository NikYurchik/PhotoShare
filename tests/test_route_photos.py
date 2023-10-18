from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.database.models import User, Photo
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
    current_user.roles = Role.admin
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]


def test_upload_photo(client, token, photo, monkeypatch):
    # with patch.object(auth_service, 'r') as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        monkeypatch.setattr('src.services.cloud_image.CloudImage.generate_name_image', MagicMock())
        monkeypatch.setattr('src.services.cloud_image.CloudImage.upload', MagicMock())
        monkeypatch.setattr('src.services.cloud_image.CloudImage.get_url_for_image', MagicMock(return_value=photo["file_url"]))

        f = './fileupload.tst'
        with open(f, 'wb') as tmp:
            tmp.write(b'upload this')
        with open(f, 'rb') as tmp:
            response = client.post(
                "/api/photos/new",
                files={"file": ("filename", tmp, "image/jpeg")},
                json=photo,
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 201, response.text
            data = response.json()
            assert data["user_id"] == photo["user_id"]
            assert data["file_url"] == photo["file_url"]
            assert data["description"] == photo["description"]
            assert "id" in data


def test_get_all_photos(client, token, user, photos, monkeypatch):
    # with patch.object(auth_service, "r") as redis_mock:
    #     redis_mock.get.return_value = None
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    #     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

        response = client.get("/api/photos/all-photos",
                              headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        data = response.json()
        assert type(data) == list
        # assert data[0]["username"] == user["username"]
        # assert data[0]["email"] == user["email"]

