from unittest.mock import MagicMock
import pytest
from sqlalchemy import insert
from fastapi.testclient import TestClient

from src.database.models import User, Photo, Comment
from src.services.roles import Role
from src.schemas import CommentModel
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


@pytest.fixture()
def cphoto(client, user, session, monkeypatch):
    user_: User = session.query(User).filter(User.email == user.get('email')).first()
    photo_: Photo = session.query(Photo).filter(Photo.user_id == user_.id).first()
    if not photo_:
        query = insert(Photo).values(
            description="photo_description",
            file_url="https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg",
            user_id=user_.id,
        ).returning(Photo)

        photo_ = session.execute(query).scalar_one()
        session.commit()

    return photo_


def test_create_comment(client, token, cphoto, monkeypatch):
    body = {"text": "Comment"}    
    response = client.post(
        f"/api/comments/{cphoto.id}",
        json=body,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["text"] == body["text"]


def test_get_comments(client, token, cphoto, session, monkeypatch):
    response = client.get(
        f"/api/comments/{cphoto.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


def test_update_comment(client, token, cphoto, session, monkeypatch):
    comment: Comment = session.query(Comment).filter(Comment.photo_id == cphoto.id).first()
    body = {"id": comment.id, "text": comment.text+"333"}    
    response = client.put(
        "/api/comments",
        json=body,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["text"] == body["text"]

    
def test_update_comment_notfound(client, token, cphoto, session, monkeypatch):
    comment: Comment = session.query(Comment).filter(Comment.photo_id == cphoto.id).first()
    body = {"id": comment.id+99, "text": comment.text+"333"}    
    response = client.put(
        "/api/comments",
        json=body,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_FOUND


def test_delete_comment(client, token, cphoto, session, monkeypatch):
    comment: Comment = session.query(Comment).filter(Comment.photo_id == cphoto.id).first()
    response = client.delete(
        f"/api/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204, response.text

# TestClient.delete()