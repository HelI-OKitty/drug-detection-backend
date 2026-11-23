from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_admin
from app.main import app

FAKE_ADMIN_ID = "665abc1234567890abcdef01"
BASE_URL = "http://test"
AUTH = {"Authorization": "Bearer token"}


def mock_admin():
    return FAKE_ADMIN_ID


def make_summary() -> dict:
    return {
        "total": 42,
        "today": 5,
        "unreviewed": 10,
        "verdict": {"positive": 42, "negative": 3},
    }


def make_analytics() -> dict:
    return {
        "trend": [
            {"date": f"2026-08-{20 + i:02d}", "positive": i + 1, "negative": 0}
            for i in range(7)
        ],
        "text": {
            "analyzed": 30,
            "top_terms": [{"term": "브액", "count": 15}],
            "top_intents": [{"intent": "판매", "count": 10}],
            "source": {"model": 20, "rule": 10},
        },
        "image": {
            "total_images": 50,
            "objects": [{"class_name": "Meth", "count": 8}],
            "ocr_with_text": 20,
            "ocr_without_text": 30,
        },
    }


def make_detection(detection_id=None) -> dict:
    return {
        "id": str(detection_id or ObjectId()),
        "platform": "x",
        "source_id": "1234567890",
        "source_url": "https://x.com/testuser/status/1234567890",
        "content": "의심 게시글",
        "created_at_source": datetime.now(timezone.utc),
        "keyword": ["마약"],
        "author_id": "testuser",
        "is_drug": True,
        "score": 0.85,
        "review_status": "unreviewed",
        "detected_at": datetime.now(timezone.utc),
    }


async def test_dashboard_summary():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch(
        "app.api.dashboard_api.get_summary", AsyncMock(return_value=make_summary())
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.get("/dashboard/summary", headers=AUTH)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "today" in data
    assert "unreviewed" in data
    assert "verdict" in data


async def test_dashboard_summary_counts():
    app.dependency_overrides[get_current_admin] = mock_admin
    summary = make_summary()

    with patch("app.api.dashboard_api.get_summary", AsyncMock(return_value=summary)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.get("/dashboard/summary", headers=AUTH)

    app.dependency_overrides.clear()
    data = resp.json()
    assert data["total"] == 42
    assert data["today"] == 5
    assert data["unreviewed"] == 10
    assert data["verdict"]["positive"] == 42
    assert data["verdict"]["negative"] == 3


async def test_dashboard_analytics():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch(
        "app.api.dashboard_api.get_analytics",
        AsyncMock(return_value=make_analytics()),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.get("/dashboard/analytics", headers=AUTH)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["trend"]) == 7
    assert "text" in data
    assert "image" in data
    assert data["text"]["analyzed"] == 30
    assert data["image"]["total_images"] == 50


async def test_dashboard_recent():
    app.dependency_overrides[get_current_admin] = mock_admin
    items = [make_detection() for _ in range(5)]

    with patch("app.api.dashboard_api.get_recent", AsyncMock(return_value=items)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.get("/dashboard/recent", headers=AUTH)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert len(resp.json()) == 5


async def test_dashboard_recent_limit():
    app.dependency_overrides[get_current_admin] = mock_admin
    items = [make_detection() for _ in range(3)]

    with patch("app.api.dashboard_api.get_recent", AsyncMock(return_value=items)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.get("/dashboard/recent?limit=3", headers=AUTH)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert len(resp.json()) == 3
