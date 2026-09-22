from fastapi import APIRouter, status

from app.schemas.ai import DetectedObject
from app.schemas.public import PublicAnalyzeRequest, PublicAnalyzeResponse
from app.services.ai_service import call_image_ai, call_text_ai

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/analyze",
    response_model=PublicAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
async def public_analyze(body: PublicAnalyzeRequest):
    image_prediction: int = 0
    detected_objects: list[DetectedObject] | None = None
    ocr_text: str | None = None
    prob_drug: float | None = None
    prob_non_drug: float | None = None

    # 1차 탐지: 이미지 AI
    if body.image:
        image_result = await call_image_ai(body.image)
        image_prediction = image_result.prediction
        if image_prediction == 1:
            detected_objects = image_result.detected_objects

        # 2차 탐지: text AI (ocr_text가 있으면 body.text에 붙여서 전달)
        ocr_text = image_result.ocr_text or None
        text_input: str | None = None
        if body.text and image_result.ocr_text:
            text_input = body.text + " " + image_result.ocr_text
        elif image_result.ocr_text:
            text_input = image_result.ocr_text
        elif body.text:
            text_input = body.text

        if text_input:
            text_result = await call_text_ai(text_input)
            text_prediction = text_result.prediction
            prob_drug = text_result.prob_drug
            prob_non_drug = text_result.prob_non_drug
        else:
            text_prediction = 0

    # 이미지 없이 텍스트만 있는 경우
    else:
        text_result = await call_text_ai(body.text)  # type: ignore[arg-type]
        text_prediction = text_result.prediction
        prob_drug = text_result.prob_drug
        prob_non_drug = text_result.prob_non_drug

    is_drug = bool(image_prediction == 1 or text_prediction == 1)

    return PublicAnalyzeResponse(
        is_drug=is_drug,
        detected_objects=detected_objects,
        ocr_text=ocr_text,
        prob_drug=prob_drug,
        prob_non_drug=prob_non_drug,
    )
