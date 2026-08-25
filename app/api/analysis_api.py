from fastapi import APIRouter, Depends, status

from app.core.security import get_current_admin
from app.schemas.analysis import (
    AnalysisImageRequest,
    AnalysisMultimodalRequest,
    AnalysisResult,
    AnalysisTextRequest,
)
from app.services.analysis_service import analyze_and_save

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/text", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
async def analyze_text(
    body: AnalysisTextRequest,
    admin_id: str = Depends(get_current_admin),
):
    text_score: float = 0.0  # TODO: AI 서버 연동
    return await analyze_and_save(
        source_url=body.source_url,
        admin_id=admin_id,
        content=body.content,
        text_score=text_score,
    )


@router.post("/image", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
async def analyze_image(
    body: AnalysisImageRequest,
    admin_id: str = Depends(get_current_admin),
):
    image_score: float = 0.0  # TODO: AI 서버 연동
    return await analyze_and_save(
        source_url=body.source_url,
        admin_id=admin_id,
        image_url=body.image_url,
        image_score=image_score,
    )


@router.post(
    "/multimodal",
    response_model=AnalysisResult,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_multimodal(
    body: AnalysisMultimodalRequest,
    admin_id: str = Depends(get_current_admin),
):
    text_score: float = 0.0   # TODO: AI 서버 연동
    image_score: float = 0.0  # TODO: AI 서버 연동
    return await analyze_and_save(
        source_url=body.source_url,
        admin_id=admin_id,
        content=body.content,
        image_url=body.image_url,
        text_score=text_score,
        image_score=image_score,
    )
