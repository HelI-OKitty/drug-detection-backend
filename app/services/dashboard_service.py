from datetime import datetime, timedelta, timezone

from app.db.mongo import db


async def get_summary(admin_id: str) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = await db.detections.count_documents({"admin_id": admin_id})
    today = await db.detections.count_documents(
        {"admin_id": admin_id, "detected_at": {"$gte": today_start}}
    )
    unconfirmed = await db.detections.count_documents(
        {"admin_id": admin_id, "review_status": "pending"}
    )

    trend = []
    for i in range(6, -1, -1):
        day_start = (today_start - timedelta(days=i)).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        count = await db.detections.count_documents(
            {"admin_id": admin_id, "detected_at": {"$gte": day_start, "$lt": day_end}}
        )
        trend.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

    return {"total": total, "today": today, "unconfirmed": unconfirmed, "trend": trend}


async def get_recent(admin_id: str, limit: int = 10) -> list[dict]:
    cursor = (
        db.detections.find({"admin_id": admin_id}).sort("detected_at", -1).limit(limit)
    )
    return [
        {
            "id": str(doc["_id"]),
            "source_url": doc["source_url"],
            "score": doc["score"],
            "review_status": doc["review_status"],
            "detected_at": doc["detected_at"],
        }
        async for doc in cursor
    ]
