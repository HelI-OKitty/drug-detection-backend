DEFAULT_KEYWORDS: list[str] = [
    "브액",
    "작대기",
    "아이스",
    "오방",
    "시원한술",
    "빙두",
    "엑스터시",
    "대마",
    "필로폰",
    "코카인",
    "술친",
]

MAX_CUSTOM_KEYWORDS = 2
MAX_KEYWORDS = len(DEFAULT_KEYWORDS) + MAX_CUSTOM_KEYWORDS  # 13

# 하위 호환용 — crawl_pipeline_service의 폴백으로만 사용
DRUG_KEYWORDS: list[str] = DEFAULT_KEYWORDS
