"""
text_ai_result가 null인 기존 탐지 문서에 대해
이미지 AI + 텍스트 AI를 재실행하여 DB를 업데이트하는 백필 스크립트

실행 방법:
    python -m scripts.backfill_ai_results
"""

import asyncio
import base64
import logging

import httpx

from app.db.mongo import db
from app.services.detection_service import analyze_content

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _download_images(image_urls: list[str]) -> list[tuple[str, str]]:
    """이미지 URL 리스트 중 다운로드 성공한 (url, base64) 쌍만 반환"""
    result: list[tuple[str, str]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in image_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    result.append((url, base64.b64encode(resp.content).decode()))
                else:
                    logger.warning(
                        "이미지 다운로드 실패 (status=%s): %s", resp.status_code, url
                    )
            except Exception:
                logger.warning("이미지 다운로드 실패: %s", url)
    return result


async def backfill():
    cursor = db.detections.find({"text_ai_result": None})
    total = 0
    success = 0
    failed = 0

    async for doc in cursor:
        total += 1
        doc_id = doc["_id"]
        content = doc.get("content")

        # image_url 목록 추출
        image_urls = [
            img["image_url"]
            for img in doc.get("image_ai_results", [])
            if img.get("image_url")
        ]

        try:
            # 이미지 다운로드 (실패한 URL은 자동 제거)
            downloaded = await _download_images(image_urls) if image_urls else []
            images = downloaded if downloaded else None

            # AI 분석
            result = await analyze_content(content, images)

            # DB 업데이트
            update: dict = {
                "is_drug": result.is_drug,
                "text_ai_result": (
                    result.text_ai_result.model_dump()
                    if result.text_ai_result
                    else None
                ),
            }

            # image_ai_results 업데이트 (ocr_text 포함)
            if result.image_ai_results:
                update["image_ai_results"] = [
                    r.model_dump(exclude={"ocr_text_results"})
                    for r in result.image_ai_results
                ]

            await db.detections.update_one(
                {"_id": doc_id},
                {"$set": update},
            )
            success += 1
            logger.info("완료: %s", doc_id)

        except Exception:
            logger.exception("실패: %s", doc_id)
            failed += 1

    logger.info("백필 완료 — 전체: %d, 성공: %d, 실패: %d", total, success, failed)


if __name__ == "__main__":
    asyncio.run(backfill())
