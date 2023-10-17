import ipaddress

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.conf import messages
import main

client = TestClient(main.app)


def test_read_main(monkeypatch):
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

    mock_ip_address = MagicMock(return_value=ipaddress.IPv4Address("127.0.0.1"))
    with patch("ipaddress.ip_address", mock_ip_address):

        response = client.get("/")
        assert response.status_code == 200, response.text


# def test_read_main_not_allowed_ip_address(monkeypatch):
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

#     mock_ip_address = MagicMock(return_value=ipaddress.IPv4Address("127.1.1.1"))
#     with patch("ipaddress.ip_address", mock_ip_address):

#         response = client.get("/")
#         assert response.status_code == 403, response.text
#         data = response.json()
#         assert data["detail"] == messages.NOT_ALLOWED_IP_ADDRESS


def test_read_main_user_agent_banned(monkeypatch):
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

    main.user_agent_ban_list.append(r"testclient")
    response = client.get("/")
    main.user_agent_ban_list.remove(r"testclient")

    assert response.status_code == 403, response.text
    data = response.json()
    assert data["detail"] == messages.YOU_ARE_BANNED


def test_main_healthchecker(monkeypatch):
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
    monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())

    response = client.get("/api/healthchecker")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == messages.WELCOME_TO_FASTAPI


# def test_main_healthchecker_bad_database(monkeypatch):
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.redis', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.identifier', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.FastAPILimiter.http_callback', AsyncMock())
#     monkeypatch.setattr('fastapi_limiter.depends.RateLimiter', AsyncMock())
#     monkeypatch.setattr('src.database.db.execute.fetchone', AsyncMock(return_result=None))

#     response = client.get("/api/healthchecker")
#     assert response.status_code == 500, response.text
#     data = response.json()
#     assert data["message"] == messages.DATABASE_IS_NOT_CONFIGURED_CORRECTLY
