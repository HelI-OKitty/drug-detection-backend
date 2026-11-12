from fastapi import APIRouter, status

from app.schemas.public import PublicAnalyzeRequest, PublicAnalyzeResponse
from app.services.detection_service import analyze_content

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/analyze",
    response_model=PublicAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
async def public_analyze(body: PublicAnalyzeRequest):
    from app.schemas.ai import ImageAIResult

    images = [("", b64) for b64 in body.images] if body.images else None
    result = await analyze_content(body.text, images)

    return PublicAnalyzeResponse(
        is_drug=result.is_drug,
        text_ai_result=result.text_ai_result,
        image_ai_results=[
            ImageAIResult(
                prediction=img.prediction,
                image_score=img.image_score,
                detected_objects=img.detected_objects,
                ocr_text=img.ocr_text,
            )
            for img in result.image_ai_results
        ],
    )
