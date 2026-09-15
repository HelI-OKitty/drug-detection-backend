from app.schemas.ai import TextAIResponse

TEXT_AI_NON_DRUG = TextAIResponse(
    text="나는 바나나를 먹는다.",
    clean_text="나는 바나나를 먹는다.",
    prediction=0,
    label="비마약",
    source="model",
    rule_triggered=False,
    prob_drug=0.0033,
    prob_non_drug=0.9967,
    prob_drug_percent=0.33,
    prob_non_drug_percent=99.67,
    matched_terms=[],
    matched_intents=[],
)

TEXT_AI_DRUG = TextAIResponse(
    text="드라퍼 구함.",
    clean_text="드라퍼 구함.",
    prediction=1,
    label="마약",
    source="rule",
    rule_triggered=True,
    prob_drug=None,
    prob_non_drug=None,
    prob_drug_percent=None,
    prob_non_drug_percent=None,
    matched_terms=["드라퍼"],
    matched_intents=["구함"],
)
