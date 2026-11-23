from app.schemas.ai import DetectedObject, ImageAIPrediction

IMAGE_AI_NON_DRUG: list[ImageAIPrediction] = [
    ImageAIPrediction(
        prediction=0,
        image_score=0.05,
        detected_objects=[],
        ocr_text="",
    )
]

IMAGE_AI_DRUG: list[ImageAIPrediction] = [
    ImageAIPrediction(
        prediction=1,
        image_score=0.97,
        detected_objects=[DetectedObject(class_name="drug", confidence=0.97)],
        ocr_text="",
    )
]

IMAGE_AI_NON_DRUG_WITH_OCR: list[ImageAIPrediction] = [
    ImageAIPrediction(
        prediction=0,
        image_score=0.12,
        detected_objects=[],
        ocr_text="드라퍼 구함.",
    )
]
