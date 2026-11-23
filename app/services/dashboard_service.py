import asyncio
from datetime import datetime, timezone

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
