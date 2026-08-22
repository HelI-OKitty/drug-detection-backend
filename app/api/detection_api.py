from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument

from app.core.security import get_current_admin
from app.db.mongo import db
from app.schemas.detection import DetectionListItem, DetectionOut, ReviewStatusUpdate

router = APIRouter(prefix="/detections", tags=["detection"])


def _to_out(doc: dict) -> DetectionOut:
    return DetectionOut(
        id=str(doc["_id"]),
        source_url=doc["source_url"],
        content=doc["content"],
        score=doc["score"],
        review_status=doc["review_status"],
        admin_id=doc["admin_id"],
        detected_at=doc["detected_at"],
    )


@router.get("", response_model=list[DetectionListItem])
async def list_detections(admin_id: str = Depends(get_current_admin)):
    cursor = db.detections.find({"admin_id": admin_id}).sort("detected_at", -1)
    return [
        DetectionListItem(
            id=str(doc["_id"]),
            source_url=doc["source_url"],
            score=doc["score"],
            review_status=doc["review_status"],
            detected_at=doc["detected_at"],
        )
        async for doc in cursor
    ]


@router.get("/{detection_id}", response_model=DetectionOut)
async def get_detection(
    detection_id: str,
    admin_id: str = Depends(get_current_admin),
):
    doc = await db.detections.find_one({"_id": ObjectId(detection_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="탐지 결과를 찾을 수 없습니다")
    return _to_out(doc)


@router.patch("/{detection_id}/status", response_model=DetectionOut)
async def update_review_status(
    detection_id: str,
    body: ReviewStatusUpdate,
    admin_id: str = Depends(get_current_admin),
):
    doc = await db.detections.find_one_and_update(
        {"_id": ObjectId(detection_id)},
        {"$set": {"review_status": body.review_status}},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="탐지 결과를 찾을 수 없습니다")
    return _to_out(doc)


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: str,
    admin_id: str = Depends(get_current_admin),
):
    result = await db.detections.delete_one({"_id": ObjectId(detection_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="탐지 결과를 찾을 수 없습니다")
