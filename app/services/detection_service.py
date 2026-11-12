import logging
from dataclasses import dataclass, field

from app.schemas.ai import OcrTextAnalysis, TextAIModelResponse
from app.schemas.detection import ImageAIResultWithUrl
from app.services.ai_service import call_image_ai, call_text_ai

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    is_drug: bool
    text_ai_result: TextAIModelResponse | None = None
    image_ai_results: list[ImageAIResultWithUrl] = field(default_factory=list)


async def analyze_content(
    text: str | None,
    images: list[tuple[str, str]] | None = None,
) -> AnalysisResult:
    """텍스트와 이미지를 AI 서버에 분석 요청하고 AnalysisResult 반환

    판정 규칙:
    - 텍스트 AI 양성(prediction=1) OR 이미지 AI 1개 이상 양성 → is_drug=True
    - AI 서버 오류 시 해당 결과를 None/건너뜀으로 처리, 나머지 결과로 판정
    - 이미지 다운로드 실패(b64 없음)는 파이프라인에서 이미 제외됨

    Args:
        text: 분석할 텍스트 (없을 수도 있음)
        images: (image_url, base64) 튜플 리스트
                public API는 image_url을 빈 문자열로 전달
    """
    text_ai_result: TextAIModelResponse | None = None
    image_ai_results: list[ImageAIResultWithUrl] = []
    image_prediction = 0

    if images:
        # (image_index, ocr_text) — OCR 텍스트를 임시로 별도 추적
        ocr_indexed: list[tuple[int, str]] = []

        for url, b64 in images:
            try:
                img_result = await call_image_ai(b64)
                idx = len(image_ai_results)
                image_ai_results.append(
                    ImageAIResultWithUrl(
                        image_url=url,
                        prediction=img_result.prediction,
                        image_score=img_result.image_score,
                        detected_objects=img_result.detected_objects,
                    )
                )
                if img_result.ocr_text:
                    ocr_indexed.append((idx, img_result.ocr_text))
                if img_result.prediction == 1:
                    image_prediction = 1
            except Exception:
                logger.warning("이미지 AI 호출 실패 (url=%s), 해당 이미지 건너뜀", url)

        ocr_texts = [t for _, t in ocr_indexed]

        if text or ocr_texts:
            try:
                text_ai_result = await call_text_ai(text, ocr_texts or None)
                # ocr_text_results를 해당 이미지에 매핑
                if text_ai_result and text_ai_result.ocr_text_results:
                    analysis_map = {
                        idx: OcrTextAnalysis(
                            ocr_text=ocr_result.text,
                            prediction=ocr_result.prediction,
                            ocr_text_score=ocr_result.prob_drug_percent,
                            matched_terms=ocr_result.matched_terms,
                            matched_intents=ocr_result.matched_intents,
                        )
                        for (idx, _), ocr_result in zip(
                            ocr_indexed, text_ai_result.ocr_text_results
                        )
                    }
                    image_ai_results = [
                        r.model_copy(
                            update={
                                "ocr_text_results": (
                                    [analysis_map[i]] if i in analysis_map else []
                                )
                            }
                        )
                        for i, r in enumerate(image_ai_results)
                    ]
            except Exception:
                logger.warning("텍스트 AI 호출 실패, 텍스트 판정 생략")

    elif text:
        try:
            text_ai_result = await call_text_ai(text)
        except Exception:
            logger.warning("텍스트 AI 호출 실패, 텍스트 판정 생략")

    text_prediction = text_ai_result.prediction if text_ai_result else 0
    is_drug = bool(image_prediction == 1 or text_prediction == 1)

    return AnalysisResult(
        is_drug=is_drug,
        text_ai_result=text_ai_result,
        image_ai_results=image_ai_results,
    )
