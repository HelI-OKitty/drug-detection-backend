from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.mocks import TEXT_AI_DRUG, TEXT_AI_NON_DRUG

BASE_URL = "http://test"


async def test_analyze_text_non_drug():
    """텍스트 전송 → 비마약 판별"""
    with patch(
        "app.api.public_api.call_text_ai", AsyncMock(return_value=TEXT_AI_NON_DRUG)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"text": "나는 바나나를 먹는다."},
            )

    assert resp.status_code == 200
    assert resp.json()["is_drug"] is False


async def test_analyze_text_drug():
    """텍스트 전송 → 마약 판별"""
    with patch("app.api.public_api.call_text_ai", AsyncMock(return_value=TEXT_AI_DRUG)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"text": "드라퍼 구함."},
            )

    assert resp.status_code == 200
    assert resp.json()["is_drug"] is True


async def test_analyze_image_only():
    """이미지만 전송 → 이미지 AI 미구현으로 501 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.post(
            "/public/analyze",
            json={"image": "base64encodedstring=="},
        )

    assert resp.status_code == 501


async def test_analyze_missing_both():
    """text, image 둘 다 없으면 → 422 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        resp = await client.post(
            "/public/analyze",
            json={},
        )

    assert resp.status_code == 422
