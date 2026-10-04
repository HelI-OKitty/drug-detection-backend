"""
공통 탐지 서비스

public API(수동 입력)와 크롤링 파이프라인(자동) 양쪽에서 재사용하는
AI 분석 + score 계산 로직을 담당한다.
"""

from dataclasses import dataclass, field

from app.schemas.ai import TextAIResponse
from app.schemas.detection import ImageAIResultWithUrl
from app.services.ai_service import call_image_ai, call_text_ai


@dataclass
class AnalysisResult:
    is_drug: bool
    score: float
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
    score = _calculate_score(text_ai_result, image_ai_results)

    return AnalysisResult(
        is_drug=is_drug,
        score=score,
        text_ai_result=text_ai_result,
        image_ai_results=image_ai_results,
    )


def _calculate_score(
    text_result: TextAIResponse | None,
    image_results: list[ImageAIResultWithUrl],
) -> float:
    """텍스트 AI + 이미지 AI 결과를 합산하여 종합 점수(0~1) 반환

    이미지 없음: 텍스트 확률값 그대로
    이미지 있음: 텍스트 60% + 이미지 최대값 40% 가중 평균
    """
    text_score = 0.0
    if text_result:
        text_score = (
            text_result.prob_drug
            if text_result.prob_drug is not None
            else float(text_result.prediction)
        )

    if not image_results:
        return round(text_score, 4)

    image_score = max(r.image_score for r in image_results)
    return round(text_score * 0.6 + image_score * 0.4, 4)
