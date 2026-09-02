from datetime import datetime, timezone

from app.db.mongo import db


async def get_threshold() -> float:
    doc = await db.configs.find_one({"key": "threshold"})
    return doc["value"] if doc else 0.5


async def get_weights() -> dict:
    doc = await db.configs.find_one({"key": "weights"})
    if doc:
        return {"text": doc["text_weight"], "image": doc["image_weight"]}
    return {"text": 0.5, "image": 0.5}


def late_fusion(
    text_score: float | None,
    image_score: float | None,
    text_weight: float,
    image_weight: float,
) -> float:
    if text_score is not None and image_score is not None:
        total = text_weight + image_weight
        return (text_score * text_weight + image_score * image_weight) / total
    if text_score is not None:
        return text_score
    if image_score is not None:
        return image_score
    return 0.0


async def analyze_and_save(
    source_url: str,
    admin_id: str,
    content: str | None = None,
    image_url: str | None = None,
    text_score: float | None = None,
    image_score: float | None = None,
) -> dict:
    threshold = await get_threshold()
    weights = await get_weights()

    final_score = late_fusion(
        text_score, image_score, weights["text"], weights["image"]
    )

    doc = {
        "source_url": source_url,
        "content": content or "",
        "image_url": image_url,
        "score": final_score,
        "text_score": text_score,
        "image_score": image_score,
        "review_status": "pending",
        "admin_id": admin_id,
        "detected_at": datetime.now(timezone.utc),
    }
    result = await db.detections.insert_one(doc)

    return {
        "detection_id": str(result.inserted_id),
        "score": final_score,
        "is_drug": final_score >= threshold,
        "text_score": text_score,
        "image_score": image_score,
    }
