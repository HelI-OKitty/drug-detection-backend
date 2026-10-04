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

    first_img = result.image_ai_results[0] if result.image_ai_results else None
    return PublicAnalyzeResponse(
        is_drug=result.is_drug,
        detected_objects=(
            first_img.detected_objects
            if first_img and first_img.prediction == 1
            else None
        ),
        ocr_text=first_img.ocr_text if first_img else None,
        prob_drug=result.text_ai_result.prob_drug if result.text_ai_result else None,
        prob_non_drug=(
            result.text_ai_result.prob_non_drug if result.text_ai_result else None
        ),
    )
