from app.schemas.ai import TextAIModelResponse

TEXT_AI_NON_DRUG = TextAIModelResponse(
    text="대마야호",
    clean_text="대마야호",
    prediction=0,
    label="비마약",
    prob_non_drug=0.9967,
    prob_drug=0.0033,
    prob_non_drug_percent=99.67,
    prob_drug_percent=0.33,
    source="model",
    rule_triggered=False,
    matched_terms=[],
    matched_intents=[],
)

TEXT_AI_DRUG = TextAIModelResponse(
    text="드라퍼 구함",
    clean_text="드라퍼 구함",
    prediction=1,
    label="마약",
    prob_non_drug=None,
    prob_drug=None,
    prob_non_drug_percent=None,
    prob_drug_percent=None,
    source="rule",
    rule_triggered=True,
    matched_terms=["드라퍼"],
    matched_intents=["구함"],
)
