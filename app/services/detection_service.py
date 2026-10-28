from dataclasses import dataclass, field

from app.schemas.ai import TextAIResponse
from app.schemas.detection import ImageAIResultWithUrl
from app.services.ai_service import call_image_ai, call_text_ai


@dataclass
class AnalysisResult:
    is_drug: bool
    text_ai_result: TextAIResponse | None = None
    image_ai_results: list[ImageAIResultWithUrl] = field(default_factory=list)


async def analyze_content(
    text: str | None,
    images: list[tuple[str, str]] | None = None,
) -> AnalysisResult:
    """텍스트와 이미지를 AI 서버에 분석 요청하고 AnalysisResult 반환

    Args:
        text: 분석할 텍스트 (없을 수도 있음)
        images: (image_url, base64) 튜플 리스트
                public API는 image_url을 빈 문자열로 전달
    """
    text_ai_result: TextAIResponse | None = None
    image_ai_results: list[ImageAIResultWithUrl] = []
    image_prediction = 0

    # 이미지 AI 처리
    if images:
        for url, b64 in images:
            img_result = await call_image_ai(b64)
            image_ai_results.append(
                ImageAIResultWithUrl(
                    image_url=url,
                    prediction=img_result.prediction,
                    image_score=img_result.image_score,
                    detected_objects=img_result.detected_objects,
                    ocr_text=img_result.ocr_text,
                )
            )
            if img_result.prediction == 1:
                image_prediction = 1

        # 모든 이미지의 OCR 텍스트 취합 후 본문과 합산
        ocr_combined = " ".join(r.ocr_text for r in image_ai_results if r.ocr_text)
        if text and ocr_combined:
            text_input: str | None = text + " " + ocr_combined
        elif ocr_combined:
            text_input = ocr_combined
        else:
            text_input = text

        if text_input:
            text_ai_result = await call_text_ai(text_input)

    # 텍스트만 있는 경우
    elif text:
        text_ai_result = await call_text_ai(text)

    text_prediction = text_ai_result.prediction if text_ai_result else 0
    is_drug = bool(image_prediction == 1 or text_prediction == 1)

    return AnalysisResult(
        is_drug=is_drug,
        text_ai_result=text_ai_result,
        image_ai_results=image_ai_results,
    )
