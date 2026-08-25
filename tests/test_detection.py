from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_admin
from app.main import app

FAKE_ADMIN_ID = "665abc1234567890abcdef01"
FAKE_ID = str(ObjectId())


def mock_admin():
    return FAKE_ADMIN_ID


def make_doc(detection_id: str | None = None) -> dict:
    return {
        "_id": ObjectId(detection_id) if detection_id else ObjectId(),
        "source_url": "https://example.com/post/1",
        "content": "의심 게시글",
        "score": 0.85,
        "review_status": "pending",
        "admin_id": FAKE_ADMIN_ID,
        "detected_at": datetime.now(timezone.utc),
    }


async def test_list_detections():
    app.dependency_overrides[get_current_admin] = mock_admin

    async def fake_cursor():
        yield make_doc()

    with patch("app.api.detection_api.db") as mock_db:
        mock_db.detections.find.return_value.sort.return_value = fake_cursor()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/detections", headers={"Authorization": "Bearer token"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_detection_not_found():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.detection_api.db") as mock_db:
        mock_db.detections.find_one = AsyncMock(return_value=None)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/detections/{FAKE_ID}", headers={"Authorization": "Bearer token"}
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 404


async def test_update_review_status():
    app.dependency_overrides[get_current_admin] = mock_admin
    doc = make_doc(FAKE_ID)
    doc["review_status"] = "confirmed"

    with patch("app.api.detection_api.db") as mock_db:
        mock_db.detections.find_one_and_update = AsyncMock(return_value=doc)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"/detections/{FAKE_ID}/status",
                json={"review_status": "confirmed"},
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["review_status"] == "confirmed"


async def test_delete_detection():
    app.dependency_overrides[get_current_admin] = mock_admin
    mock_result = MagicMock()
    mock_result.deleted_count = 1

    with patch("app.api.detection_api.db") as mock_db:
        mock_db.detections.delete_one = AsyncMock(return_value=mock_result)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(
                f"/detections/{FAKE_ID}", headers={"Authorization": "Bearer token"}
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 204
