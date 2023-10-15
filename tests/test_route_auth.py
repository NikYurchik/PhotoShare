from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from unittest.mock import MagicMock
import pytest

from src.database.models import User
from src.conf import messages
from src.services.auth import auth_service
from src.conf.config import settings


# define a function to generate a new refresh token
def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() - timedelta(days=7)
    to_encode.update({"iat": datetime.utcnow() - timedelta(days=14), "exp": expire, "scope": "refresh_token"})
    encoded_refresh_token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_refresh_token

def test_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]


def test_repeat_create_user(client, user):
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_ALREADY_EXISTS


def test_login_user_not_confirmed(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED


def test_login_user(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": 'password'},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_PASSWORD


def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": 'email', "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_EMAIL


def test_confirmed_email_is_already_confirmed(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    token_verification = auth_service.create_email_token({"sub": user.get('email')})
    response = client.get(f"/api/auth/confirmed_email/{token_verification}",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED


def test_confirmed_email_bad_request(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    token_verification = auth_service.create_email_token({"sub": 'AAA' + user.get('email')})
    response = client.get(f"/api/auth/confirmed_email/{token_verification}",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == messages.VERIFICATION_ERROR


def test_confirmed_email(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    token_verification = auth_service.create_email_token({"sub": user.get('email')})
    response = client.get(f"/api/auth/confirmed_email/{token_verification}",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == messages.EMAIL_CONFIRMED


def test_request_email_is_already_confirmed(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post(
        "/api/auth/request_email",
        json=user,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED


def test_request_email(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    response = client.post(
        "/api/auth/request_email",
        json=user,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == messages.CHECK_YOUR_EMAIL_FOR_CONFIRMATION


def test_refresh_token(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()

    token_verification = current_user.refresh_token
    response = client.get(f"/api/auth/refresh_token",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_refresh_token_could_not_validate_credential(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    token_verification = create_refresh_token({"sub": user.get('email')})
    response = client.get(f"/api/auth/refresh_token",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.COULD_NOT_VALIDATE_CREDENTIALS


def test_refresh_token_invalid_scope_for_token(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    token_verification = auth_service.create_email_token({"sub": user.get('email')})
    response = client.get(f"/api/auth/refresh_token",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_SCOPE_FOR_TOKEN


def test_refresh_token_invalid_refresh_token(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()

    token_verification = current_user.refresh_token
    current_user.refresh_token = create_refresh_token({"sub": user.get('email')}, 14)
    session.commit()

    response = client.get(f"/api/auth/refresh_token",
                            headers={"Authorization": f"Bearer {token_verification}"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_REFRESH_TOKEN


def test_login_user_banned(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    current_user.is_banned = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.YOU_ARE_BANNED


