import asyncio
import logging

import httpx

from app.core.config import settings
from app.schemas.ai import (
    ImageAIModelResponse,
    ImageAISingleResponse,
    TextAIModelResponse,
)

logger = logging.getLogger(__name__)


async def call_text_ai(
    text: str | None, ocr_texts: list[str] | None = None
) -> TextAIModelResponse:
    headers = (
        {"X-API-Key": settings.TEXT_AI_API_KEY} if settings.TEXT_AI_API_KEY else {}
    )
    body: dict = {}
    if text:
        body["text"] = text
    if ocr_texts:
        body["ocr_texts"] = ocr_texts
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.TEXT_AI_URL}/predict",
            headers=headers,
            json=body,
        )
    if response.status_code != 200 or not response.content:
        raise RuntimeError(
            f"텍스트 AI 오류 status={response.status_code} body={response.text!r}"
        )
    return TextAIModelResponse(**response.json())


async def _call_image_ai_single(
    client: httpx.AsyncClient, headers: dict, image_b64: str
) -> ImageAISingleResponse:
    response = await client.post(
        f"{settings.IMAGE_AI_URL}/predict",
        headers=headers,
        json={"image_base64": image_b64},
    )
    if response.status_code != 200 or not response.content:
        raise RuntimeError(
            f"이미지 AI 오류 status={response.status_code} body={response.text!r}"
        )
    return ImageAISingleResponse(**response.json())


async def call_image_ai(images: list[str]) -> ImageAIModelResponse:
    headers = (
        {"X-API-Key": settings.IMAGE_AI_API_KEY} if settings.IMAGE_AI_API_KEY else {}
    )
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_call_image_ai_single(client, headers, b64) for b64 in images]
        )
    return ImageAIModelResponse(
        predictions=[r.prediction for r in results],
        image_scores=[r.image_score for r in results],
        detected_objects=[r.detected_objects for r in results],
        ocr_texts=[r.ocr_texts[0] if r.ocr_texts else "" for r in results],
    )
