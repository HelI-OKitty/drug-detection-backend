from app.schemas.ai import TextAIResponse

TEXT_AI_NON_DRUG = TextAIResponse(
    prediction=0,
    source="model",
    prob_drug_percent=0.33,
    matched_terms=[],
    matched_intents=[],
)

TEXT_AI_DRUG = TextAIResponse(
    prediction=1,
    source="rule",
    prob_drug_percent=None,
    matched_terms=["드라퍼"],
    matched_intents=["구함"],
)
