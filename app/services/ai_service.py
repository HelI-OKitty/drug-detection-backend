import httpx

from app.core.config import settings
from app.schemas.ai import TextAIResponse


async def call_text_ai(text: str) -> TextAIResponse:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.TEXT_AI_URL}/predict",
            json={"text": text},
        )
    return TextAIResponse(**response.json())


# TODO: 이미지 AI 서버 호출 및 응답 구조 확정 후 구현
# async def call_image_ai(image: str) -> ImageAIResponse:
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{settings.IMAGE_AI_URL}/predict",
#             json={"image": image},
#         )
#     return ImageAIResponse(**response.json())
