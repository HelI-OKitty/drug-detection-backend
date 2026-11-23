import asyncio
from datetime import datetime, timedelta, timezone

from app.db.mongo import db


async def get_summary(admin_id: str) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    base_positive = {"admin_id": admin_id, "is_drug": True}

    total, today, unreviewed, negative = await asyncio.gather(
        db.detections.count_documents(base_positive),
        db.detections.count_documents(
            {**base_positive, "detected_at": {"$gte": today_start}}
        ),
        db.detections.count_documents(
            {**base_positive, "review_status": "unreviewed"}
        ),
        db.detections.count_documents({"admin_id": admin_id, "is_drug": False}),
    )

    return {
        "total": total,
        "today": today,
        "unreviewed": unreviewed,
        "verdict": {"positive": total, "negative": negative},
    }


async def get_analytics(admin_id: str) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    base_positive = {"admin_id": admin_id, "is_drug": True}

    trend, text, image = await asyncio.gather(
        _get_trend(admin_id, week_start, today_start),
        _get_text_analytics(base_positive),
        _get_image_analytics(base_positive),
    )

    return {"trend": trend, "text": text, "image": image}


async def _get_trend(
    admin_id: str,
    week_start: datetime,
    today_start: datetime,
) -> list[dict]:
    pipeline = [
        {
            "$match": {
                "admin_id": admin_id,
                "detected_at": {"$gte": week_start},
            }
        },
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$detected_at",
                        }
                    },
                    "is_drug": "$is_drug",
                },
                "count": {"$sum": 1},
            }
        },
    ]

    raw: dict[str, dict] = {}
    async for doc in db.detections.aggregate(pipeline):
        date = doc["_id"]["date"]
        is_drug = doc["_id"]["is_drug"]
        if date not in raw:
            raw[date] = {"positive": 0, "negative": 0}
        if is_drug:
            raw[date]["positive"] = doc["count"]
        else:
            raw[date]["negative"] = doc["count"]

    result = []
    for i in range(6, -1, -1):
        date = (today_start - timedelta(days=i)).strftime("%Y-%m-%d")
        counts = raw.get(date, {"positive": 0, "negative": 0})
        result.append({"date": date, **counts})
    return result


async def _get_text_analytics(base_positive: dict) -> dict:
    analyzed_cursor = db.detections.aggregate(
        [
            {"$match": {**base_positive, "text_ai_result": {"$ne": None}}},
            {"$count": "n"},
        ]
    )
    analyzed = 0
    async for doc in analyzed_cursor:
        analyzed = doc["n"]

    terms_pipeline = [
        {"$match": base_positive},
        {
            "$unwind": {
                "path": "$text_ai_result.matched_terms",
                "preserveNullAndEmpty": False,
            }
        },
        {"$group": {"_id": "$text_ai_result.matched_terms", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"term": "$_id", "count": 1, "_id": 0}},
    ]

    intents_pipeline = [
        {"$match": base_positive},
        {
            "$unwind": {
                "path": "$text_ai_result.matched_intents",
                "preserveNullAndEmpty": False,
            }
        },
        {"$group": {"_id": "$text_ai_result.matched_intents", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"intent": "$_id", "count": 1, "_id": 0}},
    ]

    source_pipeline = [
        {"$match": {**base_positive, "text_ai_result": {"$ne": None}}},
        {"$group": {"_id": "$text_ai_result.source", "count": {"$sum": 1}}},
    ]

    top_terms: list[dict] = []
    async for doc in db.detections.aggregate(terms_pipeline):
        top_terms.append(doc)

    top_intents: list[dict] = []
    async for doc in db.detections.aggregate(intents_pipeline):
        top_intents.append(doc)

    source: dict[str, int] = {}
    async for doc in db.detections.aggregate(source_pipeline):
        source[doc["_id"]] = doc["count"]

    return {
        "analyzed": analyzed,
        "top_terms": top_terms,
        "top_intents": top_intents,
        "source": {"model": source.get("model", 0), "rule": source.get("rule", 0)},
    }


async def _get_image_analytics(base_positive: dict) -> dict:
    img_stats_pipeline = [
        {"$match": base_positive},
        {"$unwind": {"path": "$image_ai_results", "preserveNullAndEmpty": False}},
        {
            "$group": {
                "_id": None,
                "total_images": {"$sum": 1},
                "ocr_with_text": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    {
                                        "$strLenCP": {
                                            "$ifNull": [
                                                "$image_ai_results.ocr_text",
                                                "",
                                            ]
                                        }
                                    },
                                    0,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]

    objects_pipeline = [
        {"$match": base_positive},
        {"$unwind": {"path": "$image_ai_results", "preserveNullAndEmpty": False}},
        {
            "$unwind": {
                "path": "$image_ai_results.detected_objects",
                "preserveNullAndEmpty": False,
            }
        },
        {
            "$group": {
                "_id": "$image_ai_results.detected_objects.class_name",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"class_name": "$_id", "count": 1, "_id": 0}},
    ]

    total_images = 0
    ocr_with_text = 0
    async for doc in db.detections.aggregate(img_stats_pipeline):
        total_images = doc["total_images"]
        ocr_with_text = doc["ocr_with_text"]

    objects: list[dict] = []
    async for doc in db.detections.aggregate(objects_pipeline):
        objects.append(doc)

    return {
        "total_images": total_images,
        "objects": objects,
        "ocr_with_text": ocr_with_text,
        "ocr_without_text": total_images - ocr_with_text,
    }


async def get_recent(admin_id: str, limit: int = 10) -> list[dict]:
    cursor = (
        db.detections.find({"admin_id": admin_id, "is_drug": True})
        .sort("detected_at", -1)
        .limit(limit)
    )
    return [
        {
            "id": str(doc["_id"]),
            "platform": doc["platform"],
            "source_id": doc["source_id"],
            "source_url": doc["source_url"],
            "content": doc["content"],
            "created_at_source": doc["created_at_source"],
            "keyword": doc["keyword"],
            "author_id": doc["author_id"],
            "is_drug": doc.get("is_drug", True),
            "review_status": doc["review_status"],
            "detected_at": doc["detected_at"],
        }
        async for doc in cursor
    ]
