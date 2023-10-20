from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.database.models import User, Photo
from src.services.auth import auth_service
from src.services.roles import Role
from src.conf import messages
from src import schemas


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


@pytest.fixture(scope="module")
def user2():
    return {"username": "test1",
            "email": "test1@example.com",
            "password": "123456789",
            "roles": "user",
            "is_banned": "False"
            }


@pytest.fixture()
def token2(client, user2, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    client.post("/api/auth/signup", json=user2)
    current_user: User = session.query(User).filter(User.email == user2.get('email')).first()
    current_user.confirmed = True
    current_user.roles = Role.user
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user2.get('email'), "password": user2.get('password')},
    )
    data = response.json()
    return data["access_token"]


def test_upload_photo(client, token, photo, monkeypatch):
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_image', MagicMock(return_value=photo["photo"]["file_url"]))

    f = './fileupload.tst'
    with open(f, 'wb') as tmp:
        tmp.write(b'upload this')
    with open(f, 'rb') as tmp:
        response = client.post(
            "/api/photos/new",
            files={"photo_file": ("filename", tmp, "image/jpeg")},
            data=photo["photo"],
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, response.text
        data = response.json()
        print(data)
        assert "tags" in data
        assert "photo" in data
        assert str(data["photo"]["user_id"]) == photo["photo"]["user_id"]
        assert data["photo"]["file_url"] == photo["photo"]["file_url"]
        assert data["photo"]["description"] == photo["photo"]["description"]
        assert "id" in data["photo"]


def test_get_all_photos(client, token, user, photos, monkeypatch):
    test_upload_photo(client, token, photos[1], monkeypatch)

    response = client.get("/api/photos/all",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 1
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_user(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/user/1",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 0
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_user_notfound(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/user/99",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) == 0


def test_search_photos(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/search/?keyword=es",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 0
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_id(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/single/1",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == dict
    assert len(data) > 0
    assert "tags" in data
    assert "photo" in data


def test_get_photo_by_id_notfound(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/single/999",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND


def test_update_photo_description(client, token, user, photos, monkeypatch):
    response = client.put("/api/photos/2",
                            data={"description": photos[0]["photo"]["description"]},
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == dict
    assert len(data) > 0
    assert "tags" in data
    assert "photo" in data
    assert data["photo"]["description"] == photos[0]["photo"]["description"]
    assert data["photo"]["description"] != photos[1]["photo"]["description"]


def test_update_photo_description_notfound(client, token, user, photos, monkeypatch):
    response = client.put("/api/photos/999",
                            data={"description": photos[0]["photo"]["description"]},
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND


def test_get_update_photo_description_noadmin(client, token2, user2, photos, session, monkeypatch):
    response = client.put("/api/photos/2",
                            data={"description": photos[1]["photo"]["description"]},
                            headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.OPERATION_NOT_AVAILABLE


def test_delete_photo_noadmin(client, token2, user2, photos, session, monkeypatch):
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.OPERATION_NOT_AVAILABLE


def test_delete_photo(client, token, user, photos, monkeypatch):
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204, response.text


def test_delete_photo_notfound(client, token, user, photos, monkeypatch):
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND

