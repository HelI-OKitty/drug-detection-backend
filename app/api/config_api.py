from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.db.mongo import db
from app.schemas.config import ThresholdConfig, WeightsConfig

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/threshold", response_model=ThresholdConfig)
async def get_threshold(_: str = Depends(get_current_admin)):
    doc = await db.configs.find_one({"key": "threshold"})
    return ThresholdConfig(threshold=doc["value"] if doc else 0.5)


@router.put("/threshold", response_model=ThresholdConfig)
async def set_threshold(body: ThresholdConfig, _: str = Depends(get_current_admin)):
    await db.configs.update_one(
        {"key": "threshold"},
        {"$set": {"value": body.threshold}},
        upsert=True,
    )
    return body


@router.get("/weights", response_model=WeightsConfig)
async def get_weights(_: str = Depends(get_current_admin)):
    doc = await db.configs.find_one({"key": "weights"})
    if doc:
        return WeightsConfig(
            text_weight=doc["text_weight"],
            image_weight=doc["image_weight"],
        )
    return WeightsConfig(text_weight=0.5, image_weight=0.5)


@router.put("/weights", response_model=WeightsConfig)
async def set_weights(body: WeightsConfig, _: str = Depends(get_current_admin)):
    await db.configs.update_one(
        {"key": "weights"},
        {"$set": {"text_weight": body.text_weight, "image_weight": body.image_weight}},
        upsert=True,
    )
    return body
