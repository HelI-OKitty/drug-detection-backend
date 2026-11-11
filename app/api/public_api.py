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
    images = [("", body.image)] if body.image else None
    result = await analyze_content(body.text, images)

    from app.schemas.ai import ImageAIResult

    first_img = result.image_ai_results[0] if result.image_ai_results else None
    return PublicAnalyzeResponse(
        is_drug=result.is_drug,
        text_ai_result=result.text_ai_result,
        image_ai_result=(
            ImageAIResult(
                prediction=first_img.prediction,
                image_score=first_img.image_score,
                detected_objects=first_img.detected_objects,
                ocr_text=first_img.ocr_text,
            )
            if first_img
            else None
        ),
    )
