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
    from app.schemas.ai import ImageAIResponse, OcrTextAnalysis, TextAIResponse

    images = [("", b64) for b64 in body.images] if body.images else None
    result = await analyze_content(body.text, images)

    text = result.text_ai_result
    return PublicAnalyzeResponse(
        is_drug=result.is_drug,
        text_ai_result=(
            TextAIResponse(
                prediction=text.prediction,
                source=text.source,
                text_score=text.prob_drug_percent,
                matched_terms=text.matched_terms,
                matched_intents=text.matched_intents,
                ocr_text_results=[
                    OcrTextAnalysis(
                        ocr_text=r.text,
                        prediction=r.prediction,
                        ocr_text_score=r.prob_drug_percent,
                        matched_terms=r.matched_terms,
                        matched_intents=r.matched_intents,
                    )
                    for r in text.ocr_text_results
                ],
            )
            if text
            else None
        ),
        image_ai_results=[
            ImageAIResponse(
                prediction=img.prediction,
                image_score=img.image_score,
                detected_objects=img.detected_objects,
                ocr_text_results=img.ocr_text_results,
            )
            for img in result.image_ai_results
        ],
    )
