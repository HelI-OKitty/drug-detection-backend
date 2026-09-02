from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.main import app

BASE_URL = "http://test"

ADMIN_ID = str(ObjectId())
ADMIN_EMAIL = "test@example.com"
ADMIN_NAME = "테스트관리자"
ADMIN_PASSWORD = "securePass123!"


def _make_admin_doc(password: str | None = None) -> dict:
    return {
        "_id": ObjectId(ADMIN_ID),
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "password": hash_password(password or ADMIN_PASSWORD),
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_db():
    with patch("app.services.auth_service.db") as db:
        db.admins = MagicMock()
        db.revoked_tokens = MagicMock()
        db.admins.insert_one = AsyncMock()
        db.admins.find_one = AsyncMock()
        db.admins.find_one_and_update = AsyncMock()
        db.revoked_tokens.find_one = AsyncMock()
        db.revoked_tokens.update_one = AsyncMock()
        yield db


async def test_signup_success(mock_db):
    inserted_id = ObjectId()
    mock_db.admins.insert_one.return_value = MagicMock(inserted_id=inserted_id)
    mock_db.admins.find_one.return_value = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.post(
            "/auth/signup",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "name": ADMIN_NAME,
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == ADMIN_EMAIL
    assert body["name"] == ADMIN_NAME
    assert "id" in body
    assert "created_at" in body


async def test_login_success(mock_db):
    mock_db.admins.find_one.return_value = _make_admin_doc()
    mock_db.revoked_tokens.find_one.return_value = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.post(
            "/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(mock_db):
    mock_db.admins.find_one.return_value = _make_admin_doc()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.post(
            "/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongPassword!"},
        )

    assert response.status_code == 401


async def test_refresh_with_revoked_token(mock_db):
    from app.core.security import create_refresh_token

    refresh_token = create_refresh_token(ADMIN_ID)

    import hashlib

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    mock_db.revoked_tokens.find_one.return_value = {"token_hash": token_hash}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 401


async def test_logout_registers_blacklist(mock_db):
    from app.core.security import create_refresh_token

    refresh_token = create_refresh_token(ADMIN_ID)
    access_token = create_access_token(ADMIN_ID)

    mock_db.revoked_tokens.find_one.return_value = None
    mock_db.revoked_tokens.update_one.return_value = AsyncMock()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 204
    mock_db.revoked_tokens.update_one.assert_called_once()
    call_args = mock_db.revoked_tokens.update_one.call_args
    filter_doc = call_args[0][0]
    assert "token_hash" in filter_doc
