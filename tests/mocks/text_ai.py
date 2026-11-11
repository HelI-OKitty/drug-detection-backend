from app.schemas.ai import TextAIResponse

TEXT_AI_NON_DRUG = TextAIResponse(
    prediction=0,
    source="model",
    text_score=0.33,
    matched_terms=[],
    matched_intents=[],
)

TEXT_AI_DRUG = TextAIResponse(
    prediction=1,
    source="rule",
    text_score=None,
    matched_terms=["드라퍼"],
    matched_intents=["구함"],
)
