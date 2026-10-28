"""
크롤링 파이프라인 서비스

X API 크롤링 → AI 분석 → MongoDB 저장까지의 전체 흐름을 담당한다.
"""

import logging
from datetime import datetime, timedelta, timezone

from app.db.mongo import db
from app.services.crawl_settings_service import (
    get_keywords_for_pipeline,
    get_max_results_for_pipeline,
)
from app.services.detection_service import analyze_content
from app.services.x_crawl_service import crawl_all_keywords

logger = logging.getLogger(__name__)


async def run_crawl_pipeline(
    admin_id: str,
    max_results: int | None = None,
) -> dict:
    """X API 크롤링 → AI 분석 → MongoDB 저장 파이프라인 실행

    - since_id를 DB에서 조회해 이미 크롤링한 게시글은 X API에서 아예 제외
    - 양성·음성 모두 is_drug 필드와 함께 MongoDB에 저장
    - AI/DB 실패 게시물의 source_id는 last_tweet_id 갱신에서 제외
    - 크롤링 완료 후 last_tweet_id 갱신

    Args:
        admin_id: 탐지 결과를 귀속시킬 관리자 ID
        max_results: 이번 크롤링에서 수집할 최대 게시글 수

    Returns:
        {"total": int, "saved": int, "skipped": int, "failed": int}
    """
    keywords = await get_keywords_for_pipeline(admin_id)
    if max_results is None:
        max_results = await get_max_results_for_pipeline(admin_id)

    # 마지막 크롤링 tweet ID 조회 (없으면 None → start_time 기준으로 수집)
    state = await db.crawl_state.find_one({"admin_id": admin_id})
    since_id: str | None = state["last_tweet_id"] if state else None

    posts = await crawl_all_keywords(
        keywords, max_results=max_results, since_id=since_id
    )

    saved = 0
    skipped = 0
    failed = 0
    successful_ids: list[int] = []
    failed_ids: list[int] = []

    for post in posts:
        try:
            images = (
                list(zip(post.image_urls, post.image_b64s)) if post.image_b64s else None
            )
            result = await analyze_content(post.content, images)

            doc = {
                "platform": post.platform,
                "source_id": post.source_id,
                "source_url": post.source_url,
                "content": post.content,
                "created_at_source": post.created_at_source,
                "keyword": post.matched_keywords,
                "author_id": post.author_id,
                "is_drug": result.is_drug,
                "review_status": "unreviewed",
                "text_ai_result": (
                    result.text_ai_result.model_dump()
                    if result.text_ai_result
                    else None
                ),
                "image_ai_results": [r.model_dump() for r in result.image_ai_results],
                "admin_id": admin_id,
                "detected_at": datetime.now(timezone(timedelta(hours=9))),
            }
            await db.detections.update_one(
                {"admin_id": admin_id, "source_id": post.source_id},
                {"$setOnInsert": doc},
                upsert=True,
            )
            successful_ids.append(int(post.source_id))
            if result.is_drug:
                saved += 1
            else:
                skipped += 1
        except Exception:
            logger.exception("source_id=%s 처리 실패, 건너뜀", post.source_id)
            failed_ids.append(int(post.source_id))
            failed += 1

    # since_id 갱신: 실패한 게시물이 있으면 그 중 가장 작은 ID 이전까지만 갱신
    new_last_tweet_id: str | None = None
    if successful_ids:
        if failed_ids:
            min_failed = min(failed_ids)
            safe_ids = [sid for sid in successful_ids if sid < min_failed]
            new_last_tweet_id = str(max(safe_ids)) if safe_ids else None
        else:
            new_last_tweet_id = str(max(successful_ids))

    if new_last_tweet_id and (
        since_id is None or int(new_last_tweet_id) > int(since_id)
    ):
        await db.crawl_state.update_one(
            {"admin_id": admin_id},
            {"$set": {"last_tweet_id": new_last_tweet_id}},
            upsert=True,
        )

    return {"total": len(posts), "saved": saved, "skipped": skipped, "failed": failed}
