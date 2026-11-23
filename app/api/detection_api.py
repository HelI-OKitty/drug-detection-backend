from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument

from app.core.security import get_current_admin
from app.db.mongo import db
from app.schemas.ai import OcrTextAnalysis, TextAIResponse
from app.schemas.detection import (
    DetectionListItem,
    DetectionOut,
    ImageAIDetailResponse,
    ImageAISummary,
    ReviewStatusUpdate,
)

router = APIRouter(prefix="/detections", tags=["detection"])


def _to_out(doc: dict) -> DetectionOut:
    t = doc.get("text_ai_result")
    db_ocr_results = t.get("ocr_text_results", []) if t else []

    # text_ai_result.ocr_text_results를 ocr_text가 있는 이미지 순서대로 매핑
    ocr_result_iter = iter(db_ocr_results)
    image_results = []
    for img in doc.get("image_ai_results", []):
        ocr_text_results = []
        if img.get("ocr_text"):
            ocr_result = next(ocr_result_iter, None)
            if ocr_result:
                ocr_text_results = [
                    OcrTextAnalysis(
                        ocr_text=ocr_result["text"],
                        prediction=ocr_result["prediction"],
                        ocr_text_score=ocr_result.get("prob_drug_percent"),
                        matched_terms=ocr_result.get("matched_terms", []),
                        matched_intents=ocr_result.get("matched_intents", []),
                    )
                ]
        image_results.append(
            ImageAIDetailResponse(
                image_url=img["image_url"],
                prediction=img["prediction"],
                image_score=img["image_score"],
                detected_objects=img.get("detected_objects", []),
                ocr_text_results=ocr_text_results,
            )
        )

    return DetectionOut(
        id=str(doc["_id"]),
        platform=doc["platform"],
        source_id=doc["source_id"],
        source_url=doc["source_url"],
        content=doc["content"],
        created_at_source=doc["created_at_source"],
        keyword=doc["keyword"],
        author_id=doc["author_id"],
        is_drug=doc.get("is_drug", True),
        review_status=doc["review_status"],
        text_ai_result=(
            TextAIResponse(
                prediction=t["prediction"],
                source=t["source"],
                text_score=t.get("prob_drug_percent"),
                matched_terms=t.get("matched_terms", []),
                matched_intents=t.get("matched_intents", []),
            )
            if t
            else None
        ),
        image_ai_results=image_results,
        admin_id=doc["admin_id"],
        detected_at=doc["detected_at"],
    )


@router.get("", response_model=list[DetectionListItem])
async def list_detections(admin_id: str = Depends(get_current_admin)):
    cursor = db.detections.find({"admin_id": admin_id}).sort("detected_at", -1)
    return [
        DetectionListItem(
            id=str(doc["_id"]),
            platform=doc["platform"],
            source_id=doc["source_id"],
            source_url=doc["source_url"],
            content=doc["content"],
            created_at_source=doc["created_at_source"],
            keyword=doc["keyword"],
            author_id=doc["author_id"],
            is_drug=doc.get("is_drug", True),
            review_status=doc["review_status"],
            text_ai_result=(
                TextAIResponse(
                    prediction=t["prediction"],
                    source=t["source"],
                    text_score=t.get("prob_drug_percent"),
                    matched_terms=t.get("matched_terms", []),
                    matched_intents=t.get("matched_intents", []),
                )
                if (t := doc.get("text_ai_result"))
                else None
            ),
            image_ai_results=[
                ImageAISummary(
                    prediction=img["prediction"],
                    image_score=img["image_score"],
                    has_ocr_text=bool(img.get("ocr_text")),
                )
                for img in doc.get("image_ai_results", [])
            ],
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="탐지 결과를 찾을 수 없습니다",
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="탐지 결과를 찾을 수 없습니다",
        )
    return _to_out(doc)


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: str,
    admin_id: str = Depends(get_current_admin),
):
    result = await db.detections.delete_one({"_id": ObjectId(detection_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="탐지 결과를 찾을 수 없습니다",
        )
