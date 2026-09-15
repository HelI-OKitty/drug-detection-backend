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


def _make_admin_doc(**kwargs) -> dict:
    base = {
        "_id": ObjectId(ADMIN_ID),
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "password": hash_password(ADMIN_PASSWORD),
        "created_at": datetime.now(timezone.utc),
    }
    base.update(kwargs)
    return base


@pytest.fixture
def mock_db():
    with patch("app.services.profile_service.db") as db:
        db.admins = MagicMock()
        db.admins.find_one = AsyncMock()
        db.admins.find_one_and_update = AsyncMock()
        yield db


@pytest.fixture
def access_token():
    return create_access_token(ADMIN_ID)


async def test_get_profile(mock_db, access_token):
    mock_db.admins.find_one.return_value = _make_admin_doc()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.get(
            "/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == ADMIN_EMAIL
    assert body["name"] == ADMIN_NAME
    assert body["site_url"] is None
    assert body["notification_enabled"] is False
    assert body["notification_email"] is None


async def test_get_profile_with_settings(mock_db, access_token):
    mock_db.admins.find_one.return_value = _make_admin_doc(
        site_url="https://example.com",
        notification_enabled=True,
        notification_email="alert@example.com",
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.get(
            "/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_url"] == "https://example.com"
    assert body["notification_enabled"] is True
    assert body["notification_email"] == "alert@example.com"


async def test_patch_profile_name(mock_db, access_token):
    updated_doc = _make_admin_doc(name="새이름")
    mock_db.admins.find_one.return_value = _make_admin_doc()
    mock_db.admins.find_one_and_update.return_value = updated_doc

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.patch(
            "/profile",
            json={"name": "새이름"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["name"] == "새이름"


async def test_patch_profile_password_success(mock_db, access_token):
    mock_db.admins.find_one.return_value = _make_admin_doc()
    mock_db.admins.find_one_and_update.return_value = _make_admin_doc()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.patch(
            "/profile",
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": "newPassword123!",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200


async def test_patch_profile_password_wrong_current(mock_db, access_token):
    mock_db.admins.find_one.return_value = _make_admin_doc()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.patch(
            "/profile",
            json={
                "current_password": "wrongPassword!",
                "new_password": "newPassword123!",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 401


async def test_patch_profile_new_password_without_current(mock_db, access_token):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.patch(
            "/profile",
            json={"new_password": "newPassword123!"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 422


async def test_patch_profile_site_url(mock_db, access_token):
    updated_doc = _make_admin_doc(site_url="https://new-site.com")
    mock_db.admins.find_one.return_value = _make_admin_doc()
    mock_db.admins.find_one_and_update.return_value = updated_doc

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.patch(
            "/profile",
            json={"site_url": "https://new-site.com"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["site_url"] == "https://new-site.com"


async def test_get_profile_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.get("/profile")

    assert resp.status_code == 401
