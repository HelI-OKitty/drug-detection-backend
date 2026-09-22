from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.mocks import (
    IMAGE_AI_DRUG,
    IMAGE_AI_NON_DRUG,
    IMAGE_AI_NON_DRUG_WITH_OCR,
    TEXT_AI_DRUG,
    TEXT_AI_NON_DRUG,
)

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
    data = resp.json()
    assert data["is_drug"] is False
    assert data["detected_objects"] is None
    assert data["ocr_text"] is None
    assert data["prob_drug"] == TEXT_AI_NON_DRUG.prob_drug
    assert data["prob_non_drug"] == TEXT_AI_NON_DRUG.prob_non_drug


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
    data = resp.json()
    assert data["is_drug"] is True
    assert data["detected_objects"] is None
    assert data["ocr_text"] is None


async def test_analyze_image_only_non_drug():
    """이미지만 전송, OCR 없음 → 비마약 판별 (텍스트 AI 미호출)"""
    with patch(
        "app.api.public_api.call_image_ai", AsyncMock(return_value=IMAGE_AI_NON_DRUG)
    ) as mock_image, patch(
        "app.api.public_api.call_text_ai", AsyncMock(return_value=TEXT_AI_NON_DRUG)
    ) as mock_text:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"image": "base64encodedstring=="},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_drug"] is False
    assert data["detected_objects"] is None
    assert data["ocr_text"] is None
    mock_image.assert_awaited_once()
    mock_text.assert_not_awaited()


async def test_analyze_image_only_drug():
    """이미지만 전송, OCR 없음 → 이미지 AI 마약 탐지"""
    with patch(
        "app.api.public_api.call_image_ai", AsyncMock(return_value=IMAGE_AI_DRUG)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"image": "base64encodedstring=="},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_drug"] is True
    assert data["detected_objects"] is not None
    assert len(data["detected_objects"]) == 1
    assert data["detected_objects"][0]["class_name"] == "drug"


async def test_analyze_image_with_ocr_drug():
    """이미지 전송 + OCR 텍스트 있음 → OCR 텍스트로 텍스트 AI 호출 → 마약 판별"""
    with patch(
        "app.api.public_api.call_image_ai",
        AsyncMock(return_value=IMAGE_AI_NON_DRUG_WITH_OCR),
    ), patch(
        "app.api.public_api.call_text_ai", AsyncMock(return_value=TEXT_AI_DRUG)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"image": "base64encodedstring=="},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_drug"] is True
    assert data["ocr_text"] == IMAGE_AI_NON_DRUG_WITH_OCR.ocr_text


async def test_analyze_image_and_text_drug():
    """이미지 + 텍스트 전송 → 텍스트 AI에 합산 입력 → 마약 판별"""
    with patch(
        "app.api.public_api.call_image_ai",
        AsyncMock(return_value=IMAGE_AI_NON_DRUG_WITH_OCR),
    ), patch(
        "app.api.public_api.call_text_ai", AsyncMock(return_value=TEXT_AI_DRUG)
    ) as mock_text:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            resp = await client.post(
                "/public/analyze",
                json={"image": "base64encodedstring==", "text": "추가 텍스트"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_drug"] is True
    # 텍스트 AI는 body.text + ocr_text 합산으로 호출됨
    call_arg = mock_text.call_args[0][0]
    assert "추가 텍스트" in call_arg
    assert IMAGE_AI_NON_DRUG_WITH_OCR.ocr_text in call_arg


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
