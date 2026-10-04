"""
크롤링 파이프라인 서비스

X API 크롤링 → AI 분석 → MongoDB 저장까지의 전체 흐름을 담당한다.
"""

from datetime import datetime, timezone

from app.core.keywords import DRUG_KEYWORDS
from app.db.mongo import db
from app.services.detection_service import analyze_content
from app.services.x_crawl_service import DEFAULT_MAX_RESULTS, crawl_all_keywords


async def run_crawl_pipeline(
    admin_id: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict:
    """X API 크롤링 → AI 분석 → MongoDB 저장 파이프라인 실행

    - since_id를 DB에서 조회해 이미 크롤링한 게시글은 X API에서 아예 제외
    - is_drug=True인 경우만 MongoDB에 저장
    - 크롤링 완료 후 last_tweet_id 갱신

    Args:
        admin_id: 탐지 결과를 귀속시킬 관리자 ID
        max_results: 이번 크롤링에서 수집할 최대 게시글 수

    Returns:
        {"total": int, "saved": int, "skipped": int}

    TODO: keywords를 DRUG_KEYWORDS 상수 대신 DB에서 admin별로 조회하도록 변경
    """
    keywords = DRUG_KEYWORDS  # TODO: DB 기반 admin별 키워드로 교체

    # 마지막 크롤링 tweet ID 조회 (없으면 None → start_time 기준으로 수집)
    state = await db.crawl_state.find_one({"admin_id": admin_id})
    since_id: str | None = state["last_tweet_id"] if state else None

    posts = await crawl_all_keywords(
        keywords, max_results=max_results, since_id=since_id
    )

    saved = 0
    skipped = 0
    last_tweet_id = since_id

    for post in posts:
        # 수집된 게시글 중 최신 tweet ID 추적
        if last_tweet_id is None or int(post.source_id) > int(last_tweet_id):
            last_tweet_id = post.source_id

        # AI 분석
        images = (
            list(zip(post.image_urls, post.image_b64s)) if post.image_b64s else None
        )
        result = await analyze_content(post.content, images)

        # 마약으로 탐지된 경우만 저장
        if not result.is_drug:
            skipped += 1
            continue

        doc = {
            "platform": post.platform,
            "source_id": post.source_id,
            "source_url": post.source_url,
            "content": post.content,
            "created_at_source": post.created_at_source,
            "keyword": post.matched_keywords,
            "author_id": post.author_id,
            "score": result.score,
            "review_status": "unreviewed",
            "text_ai_result": (
                result.text_ai_result.model_dump() if result.text_ai_result else None
            ),
            "image_ai_results": [r.model_dump() for r in result.image_ai_results],
            "admin_id": admin_id,
            "detected_at": datetime.now(timezone.utc),
        }
        await db.detections.insert_one(doc)
        saved += 1

    # 수집된 게시글이 있으면 last_tweet_id 갱신
    if last_tweet_id and last_tweet_id != since_id:
        await db.crawl_state.update_one(
            {"admin_id": admin_id},
            {"$set": {"last_tweet_id": last_tweet_id}},
            upsert=True,
        )

    return {"total": len(posts), "saved": saved, "skipped": skipped}
