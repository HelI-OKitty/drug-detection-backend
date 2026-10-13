from app.core.keywords import DEFAULT_KEYWORDS
from app.db.mongo import db
from app.schemas.crawl_settings import CrawlSettingsOut, CrawlSettingsUpdate


async def _get_or_create(admin_id: str) -> dict:
    doc = await db.crawl_settings.find_one({"admin_id": admin_id})
    if doc:
        return doc
    default = {
        "admin_id": admin_id,
        "keywords": DEFAULT_KEYWORDS,
        "max_results": 100,
        "crawl_enabled": False,
    }
    await db.crawl_settings.insert_one(default)
    return default


async def get_settings(admin_id: str) -> CrawlSettingsOut:
    doc = await _get_or_create(admin_id)
    return CrawlSettingsOut(
        keywords=doc["keywords"],
        max_results=doc["max_results"],
        crawl_enabled=doc["crawl_enabled"],
    )


async def update_settings(admin_id: str, data: CrawlSettingsUpdate) -> CrawlSettingsOut:
    doc = await _get_or_create(admin_id)
    update: dict = {}

    if data.keywords is not None:
        update["keywords"] = data.keywords

    if data.max_results is not None:
        update["max_results"] = data.max_results

    if update:
        await db.crawl_settings.update_one({"admin_id": admin_id}, {"$set": update})
        doc.update(update)

    return CrawlSettingsOut(
        keywords=doc["keywords"],
        max_results=doc["max_results"],
        crawl_enabled=doc["crawl_enabled"],
    )


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
