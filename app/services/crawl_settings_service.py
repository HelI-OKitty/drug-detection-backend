from pymongo.errors import DuplicateKeyError

from app.core.keywords import DEFAULT_KEYWORDS
from app.db.mongo import db
from app.schemas.crawl_settings import (
    CrawlEnabledToggle,
    CrawlSettingsOut,
    CrawlSettingsUpdate,
)
from app.services import gcp_scheduler_service

DEFAULT_SCHEDULE_INTERVAL = 60  # 분 단위 기본값: 1시간


async def _get_or_create(admin_id: str) -> dict:
    doc = await db.crawl_settings.find_one({"admin_id": admin_id})
    if doc:
        return doc
    default = {
        "admin_id": admin_id,
        "keywords": DEFAULT_KEYWORDS,
        "max_results": 100,
        "crawl_enabled": False,
        "schedule_interval": DEFAULT_SCHEDULE_INTERVAL,
    }
    try:
        await db.crawl_settings.insert_one(default)
    except DuplicateKeyError:
        doc = await db.crawl_settings.find_one({"admin_id": admin_id})
        return doc  # type: ignore[return-value]
    return default


def _to_out(doc: dict) -> CrawlSettingsOut:
    return CrawlSettingsOut(
        keywords=doc["keywords"],
        max_results=doc["max_results"],
        crawl_enabled=doc["crawl_enabled"],
        schedule_interval=doc.get("schedule_interval", DEFAULT_SCHEDULE_INTERVAL),
    )


async def get_settings(admin_id: str) -> CrawlSettingsOut:
    doc = await _get_or_create(admin_id)
    return _to_out(doc)


async def update_settings(admin_id: str, data: CrawlSettingsUpdate) -> CrawlSettingsOut:
    doc = await _get_or_create(admin_id)
    update: dict = {}

    if data.keywords is not None:
        update["keywords"] = data.keywords

    if data.max_results is not None:
        update["max_results"] = data.max_results

    if data.schedule_interval is not None:
        update["schedule_interval"] = data.schedule_interval

    if update:
        await db.crawl_settings.update_one({"admin_id": admin_id}, {"$set": update})
        doc.update(update)

        if data.schedule_interval is not None and doc.get("crawl_enabled"):
            await gcp_scheduler_service.update_job(admin_id, data.schedule_interval)

    return _to_out(doc)


async def toggle_crawl_enabled(
    admin_id: str, data: CrawlEnabledToggle
) -> CrawlSettingsOut:
    doc = await _get_or_create(admin_id)
    current_enabled = doc.get("crawl_enabled", False)

    if data.crawl_enabled == current_enabled:
        return _to_out(doc)

    if data.crawl_enabled:
        latest = await db.detections.find_one(
            {"admin_id": admin_id},
            sort=[("source_id", -1)],
        )
        if latest:
            await db.crawl_state.update_one(
                {"admin_id": admin_id},
                {"$set": {"last_tweet_id": latest["source_id"]}},
                upsert=True,
            )
        else:
            await db.crawl_state.delete_one({"admin_id": admin_id})
        schedule_interval = doc.get("schedule_interval", DEFAULT_SCHEDULE_INTERVAL)
        await gcp_scheduler_service.create_job(admin_id, schedule_interval)
    else:
        await gcp_scheduler_service.delete_job(admin_id)

    await db.crawl_settings.update_one(
        {"admin_id": admin_id}, {"$set": {"crawl_enabled": data.crawl_enabled}}
    )
    doc["crawl_enabled"] = data.crawl_enabled
    return _to_out(doc)


async def get_keywords_for_pipeline(admin_id: str) -> list[str]:
    doc = await db.crawl_settings.find_one({"admin_id": admin_id})
    if not doc:
        return DEFAULT_KEYWORDS
    return doc.get("keywords", DEFAULT_KEYWORDS)


async def get_max_results_for_pipeline(admin_id: str) -> int:
    doc = await db.crawl_settings.find_one({"admin_id": admin_id})
    if not doc:
        return 100
    return doc.get("max_results", 100)
