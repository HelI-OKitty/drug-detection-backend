from app.schemas.ai import DetectedObject, ImageAIModelResponse

IMAGE_AI_NON_DRUG = ImageAIModelResponse(
    predictions=[0],
    image_scores=[0.05],
    detected_objects=[[]],
    ocr_texts=[""],
)

IMAGE_AI_DRUG = ImageAIModelResponse(
    predictions=[1],
    image_scores=[0.97],
    detected_objects=[
        [DetectedObject(class_name="drug", confidence=0.97)],
    ],
    ocr_texts=[""],
)

IMAGE_AI_NON_DRUG_WITH_OCR = ImageAIModelResponse(
    predictions=[0],
    image_scores=[0.12],
    detected_objects=[[]],
    ocr_texts=["드라퍼 구함."],
)
