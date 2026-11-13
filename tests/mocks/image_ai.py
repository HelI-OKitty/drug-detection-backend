from app.schemas.ai import DetectedObject, ImageAIModelResponse

IMAGE_AI_NON_DRUG = ImageAIModelResponse(
    prediction=0,
    image_score=0.05,
    detected_objects=[],
    ocr_text="",
)

IMAGE_AI_DRUG = ImageAIModelResponse(
    prediction=1,
    image_score=0.97,
    detected_objects=[
        DetectedObject(class_name="drug", confidence=0.97),
    ],
    ocr_text="",
)

IMAGE_AI_NON_DRUG_WITH_OCR = ImageAIModelResponse(
    prediction=0,
    image_score=0.12,
    detected_objects=[],
    ocr_text="드라퍼 구함.",
)
