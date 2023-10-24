from unittest.mock import MagicMock
import pytest

from src.database.models import User, UserRole
from src.conf import messages
from src import schemas


@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    current_user.roles = UserRole.admin
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
    current_user.roles = UserRole.user
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user2.get('email'), "password": user2.get('password')},
    )
    data = response.json()
    return data["access_token"]


def test_upload_photo(client, token, photo_request, photo, monkeypatch):
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_image', MagicMock(return_value=photo["photo"]["file_url"]))

    body = str(photo_request).replace("'", '"')

    f = './fileupload.tst'
    with open(f, 'wb') as tmp:
        tmp.write(b'upload this')
    with open(f, 'rb') as tmp:
        response = client.post(
            "/api/photos",
            files={"photo_file": ("filename", tmp, "image/jpeg")},
            data={"body": body},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert "tags" in data
        assert "photo" in data
        assert str(data["photo"]["user_id"]) == photo["photo"]["user_id"]
        assert data["photo"]["file_url"] == photo["photo"]["file_url"]
        assert data["photo"]["description"] == photo["photo"]["description"]
        assert "id" in data["photo"]


def test_get_all_photos(client, token, user, photo_request, photos, monkeypatch):
    photo_request["description"] = photos[1]["photo"]["description"]
    test_upload_photo(client, token, photo_request, photos[1], monkeypatch)

    response = client.get("/api/photos",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 1
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_user(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/?user_id=1",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 0
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_user_notfound(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/?user_id=999",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) == 0


def test_search_photos(client, token, user, photos, monkeypatch):
    body = {
            "keyword": "es",
            "tag": "tags1",
            "order_by": ""
            }
    
    response = client.get("/api/photos/?keyword=es&tag=tags1",
                            params=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list
    assert len(data) > 0
    assert "tags" in data[0]
    assert "photo" in data[0]


def test_get_photo_by_id(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/1",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == dict
    assert len(data) > 0
    assert "tags" in data
    assert "photo" in data


def test_get_photo_by_id_notfound(client, token, user, photos, monkeypatch):
    response = client.get("/api/photos/999",
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND


def test_update_photo_description(client, token, user, photos, monkeypatch):
    body = {"description": photos[0]["photo"]["description"]}
    response = client.put("/api/photos/2",
                            json=body,
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
    body = {"description": photos[0]["photo"]["description"]}
    response = client.put("/api/photos/999",
                            json=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND


def test_update_photo_description_noadmin(client, token2, user2, photos, session, monkeypatch):
    body = {"description": photos[0]["photo"]["description"]}
    response = client.put("/api/photos/2",
                            json=body,
                            headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.OPERATION_NOT_AVAILABLE


def test_photo_transform(client, token, user, photo, monkeypatch):
    body = {
    "gravity": "center",
    "height": "800",
    "width": "800",
    "crop": "fill",
    "radius": "0",
    "effect": "",
    "quality": "auto",
    "fetch_format": ""
    }
    trans_url = "https://res.cloudinary.com/dqglsxwms/image/upload/c_fill,g_center,h_800,w_800/r_0/q_auto/f_jpg/v1/upload/d7pxlzuvmhossf46zxug"
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_transform_image', MagicMock(return_value=trans_url))

    response = client.post(f"/api/photos/{photo['photo']['id']}/transform",
                            json=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == dict
    assert len(data) > 0
    assert data["file_url"] == trans_url
    # assert data["photo_id"] == 1
    assert "id" in data


def test_photo_transform_notfound(client, token, user, photo, monkeypatch):
    body = {
    "gravity": "center",
    "height": "800",
    "width": "800",
    "crop": "fill",
    "radius": "0",
    "effect": "",
    "quality": "auto",
    "fetch_format": ""
    }
    trans_url = "https://res.cloudinary.com/dqglsxwms/image/upload/c_fill,g_center,h_800,w_800/r_0/q_auto/f_jpg/v1/upload/d7pxlzuvmhossf46zxug"
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_transform_image', MagicMock(return_value=trans_url))

    response = client.post("/api/photos/999/transform",
                            json=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND


def test_photo_transform_notoperation(client, token2, user2, photo, monkeypatch):
    body = {
    "gravity": "center",
    "height": "800",
    "width": "800",
    "crop": "fill",
    "radius": "0",
    "effect": "",
    "quality": "auto",
    "fetch_format": ""
    }
    trans_url = "https://res.cloudinary.com/dqglsxwms/image/upload/c_fill,g_center,h_800,w_800/r_0/q_auto/f_jpg/v1/upload/d7pxlzuvmhossf46zxug"
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_transform_image', MagicMock(return_value=trans_url))

    response = client.post("/api/photos/1/transform",
                            json=body,
                            headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.OPERATION_NOT_AVAILABLE


def test_create_qrcode(client, token, user, photo, monkeypatch):
    body = {
        "fill_color": "black",
        "back_color": "white"
    }
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_qrcode', MagicMock(return_value=photo["photo"]["qr_url"]))

    response = client.post("/api/photos/1/qrcode",
                            json=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert "tags" in data
    assert "photo" in data
    assert data["photo"]["qr_url"] == photo["photo"]["qr_url"]


def test_create_trans_qrcode(client, token, user, photo, monkeypatch):
    body = {
        "fill_color": "black",
        "back_color": "white"
    }
    qr_url = "http://res.cloudinary.com/dqglsxwms/image/upload/v1697928381/upload/qr/c8.png"
    monkeypatch.setattr('src.services.cloud_image.CloudImage.upload_qrcode', MagicMock(return_value=qr_url))

    response = client.post(f"/api/photos/{photo['photo']['id']}/qrcode/1",
                            json=body,
                            headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["qr_url"] == qr_url


def test_delete_transform_photo(client, token, user, photo, monkeypatch):
    monkeypatch.setattr('src.services.cloud_image.CloudImage.delete_image', MagicMock(return_value=None))
    
    response = client.delete(f"/api/photos/{photo['photo']['id']}/1",
                                headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204, response.text


def test_delete_photo_noadmin(client, token2, user2, photos, session, monkeypatch):
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.OPERATION_NOT_AVAILABLE


def test_delete_photo(client, token, user, photo, monkeypatch):
    photo['photo']['id'] = 2
    test_photo_transform(client, token, user, photo, monkeypatch)
    test_create_qrcode(client, token, user, photo, monkeypatch)

    monkeypatch.setattr('src.services.cloud_image.CloudImage.delete_image', MagicMock(return_value=None))
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204, response.text


def test_delete_photo_notfound(client, token, user, photos, monkeypatch):
    response = client.delete("/api/photos/2",
                                headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.PHOTO_NOT_FOUND



