import logging

import httpx

from app.core.config import settings
from app.schemas.ai import ImageAIModelResponse, TextAIModelResponse

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


async def call_image_ai(image: str) -> ImageAIModelResponse:
    headers = (
        {"X-API-Key": settings.IMAGE_AI_API_KEY} if settings.IMAGE_AI_API_KEY else {}
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.IMAGE_AI_URL}/predict",
            headers=headers,
            json={"image_base64": image},
        )
    if response.status_code != 200 or not response.content:
        raise RuntimeError(
            f"이미지 AI 오류 status={response.status_code} body={response.text!r}"
        )
    return ImageAIModelResponse(**response.json())
