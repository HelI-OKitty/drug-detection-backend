from app.schemas.ai import DetectedObject, ImageAIResponse

IMAGE_AI_NON_DRUG = ImageAIResponse(
    prediction=0,
    image_score=0.05,
    detected_objects=[],
    ocr_text="",
)

IMAGE_AI_DRUG = ImageAIResponse(
    prediction=1,
    image_score=0.97,
    detected_objects=[
        DetectedObject(class_name="drug", confidence=0.97),
    ],
    ocr_text="",
)

IMAGE_AI_NON_DRUG_WITH_OCR = ImageAIResponse(
    prediction=0,
    image_score=0.12,
    detected_objects=[],
    ocr_text="드라퍼 구함.",
)
