from fastapi import APIRouter, HTTPException, status

from app.schemas.public import PublicAnalyzeRequest, PublicAnalyzeResponse
from app.services.ai_service import call_text_ai

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/analyze",
    response_model=PublicAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
async def public_analyze(body: PublicAnalyzeRequest):
    is_drug = False

    # TODO: 이미지 AI 호출 및 탐지 로직 확정 후 구현
    if body.image and not body.text:
        raise HTTPException(
            status_code=501, detail="이미지 분석은 아직 지원되지 않습니다."
        )

    if body.text:
        result = await call_text_ai(body.text)
        is_drug = result.prediction == 1

    return PublicAnalyzeResponse(is_drug=is_drug)
