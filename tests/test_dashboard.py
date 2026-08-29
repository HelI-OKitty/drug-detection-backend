from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_admin
from app.main import app

FAKE_ADMIN_ID = "665abc1234567890abcdef01"


def mock_admin():
    return FAKE_ADMIN_ID


def make_summary() -> dict:
    return {
        "total": 42,
        "today": 5,
        "unconfirmed": 10,
        "trend": [
            {"date": f"2026-08-{20+i:02d}", "count": i + 1} for i in range(7)
        ],
    }


def make_detection(detection_id=None) -> dict:
    return {
        "id": str(detection_id or ObjectId()),
        "source_url": "https://example.com/post/1",
        "score": 0.85,
        "review_status": "pending",
        "detected_at": datetime.now(timezone.utc),
    }


async def test_dashboard_summary():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.dashboard_api.get_summary", AsyncMock(return_value=make_summary())):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/dashboard/summary", headers={"Authorization": "Bearer token"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "today" in data
    assert "unconfirmed" in data
    assert len(data["trend"]) == 7


async def test_dashboard_summary_counts():
    app.dependency_overrides[get_current_admin] = mock_admin
    summary = make_summary()

    with patch("app.api.dashboard_api.get_summary", AsyncMock(return_value=summary)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/dashboard/summary", headers={"Authorization": "Bearer token"})

    app.dependency_overrides.clear()
    data = resp.json()
    assert data["total"] == 42
    assert data["today"] == 5
    assert data["unconfirmed"] == 10


async def test_dashboard_recent():
    app.dependency_overrides[get_current_admin] = mock_admin
    items = [make_detection() for _ in range(5)]

    with patch("app.api.dashboard_api.get_recent", AsyncMock(return_value=items)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/dashboard/recent", headers={"Authorization": "Bearer token"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert len(resp.json()) == 5


async def test_dashboard_recent_limit():
    app.dependency_overrides[get_current_admin] = mock_admin
    items = [make_detection() for _ in range(3)]

    with patch("app.api.dashboard_api.get_recent", AsyncMock(return_value=items)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/dashboard/recent?limit=3", headers={"Authorization": "Bearer token"}
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert len(resp.json()) == 3
