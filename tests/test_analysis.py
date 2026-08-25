from unittest.mock import AsyncMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_admin
from app.main import app
from app.services.analysis_service import late_fusion

FAKE_ADMIN_ID = "665abc1234567890abcdef01"


def mock_admin():
    return FAKE_ADMIN_ID


def make_result(text_score=None, image_score=None) -> dict:
    return {
        "detection_id": str(ObjectId()),
        "score": 0.6,
        "is_drug": True,
        "text_score": text_score,
        "image_score": image_score,
    }


async def test_analyze_text():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.analysis_api.analyze_and_save", AsyncMock(return_value=make_result(text_score=0.6))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/analysis/text",
                json={"source_url": "https://example.com/1", "content": "의심 텍스트"},
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 201
    assert "detection_id" in resp.json()


async def test_analyze_image():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.analysis_api.analyze_and_save", AsyncMock(return_value=make_result(image_score=0.7))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/analysis/image",
                json={"source_url": "https://example.com/1", "image_url": "https://img.example.com/1.jpg"},
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 201


async def test_analyze_multimodal():
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.analysis_api.analyze_and_save", AsyncMock(return_value=make_result(text_score=0.6, image_score=0.7))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/analysis/multimodal",
                json={
                    "source_url": "https://example.com/1",
                    "content": "의심 텍스트",
                    "image_url": "https://img.example.com/1.jpg",
                },
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 201


def test_late_fusion_text_only():
    score = late_fusion(text_score=0.8, image_score=None, text_weight=0.5, image_weight=0.5)
    assert score == 0.8


def test_late_fusion_weighted():
    score = late_fusion(text_score=0.8, image_score=0.4, text_weight=0.6, image_weight=0.4)
    expected = (0.8 * 0.6 + 0.4 * 0.4) / (0.6 + 0.4)
    assert abs(score - expected) < 1e-9
