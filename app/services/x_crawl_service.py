"""
X(트위터) API v2 크롤링 서비스

흐름:
  OR 쿼리 생성 → X API 1회 호출 → 트윗 파싱 → 매칭 키워드 태깅
  → 이미지 다운로드(base64) → ParsedPost 반환
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings
from app.core.keywords import DRUG_KEYWORDS

KST = timezone(timedelta(hours=9))

X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
X_TWEET_URL = "https://api.x.com/2/tweets"
PLATFORM = "x"
CRAWL_WINDOW_HOURS = 1  # 크롤링 기준 시간 범위 (1시간 주기 스케줄링 기준)
DEFAULT_MAX_RESULTS = 100  # 기본 최대 수집 건수

# X API search/recent max_results 파라미터 허용 범위 (X API 스펙 고정값)
_X_MAX_RESULTS_PER_PAGE = 100
_X_MIN_RESULTS_PER_PAGE = 10

# 즉시 중단 대상 HTTP 상태 코드 (계속 호출해도 의미 없는 에러)
_FATAL_STATUS_CODES = {
    401,  # 인증 실패 (잘못된 토큰)
    403,  # 권한 없음
    429,  # 요청 한도 초과
}

TWEET_FIELDS = [
    "id",
    "text",
    "author_id",
    "created_at",
    "lang",
    "public_metrics",
    "possibly_sensitive",
    "conversation_id",
    "referenced_tweets",
    "entities",
    "attachments",
    "edit_history_tweet_ids",
]

EXPANSIONS = [
    "author_id",
    "attachments.media_keys",
    "referenced_tweets.id",
    "referenced_tweets.id.author_id",
]

USER_FIELDS = [
    "id",
    "name",
    "username",
    "created_at",
    "description",
    "profile_image_url",
    "verified",
    "public_metrics",
]

MEDIA_FIELDS = [
    "media_key",
    "type",
    "url",
    "preview_image_url",
    "width",
    "height",
    "duration_ms",
    "public_metrics",
]


@dataclass
class ParsedPost:
    """플랫폼에 무관한 크롤링 결과 단위 — 나중에 다른 사이트도 이 구조로 맞춤"""

    platform: str
    source_id: str
    source_url: str
    content: str
    created_at_source: datetime
    author_id: str
    image_urls: list[str] = field(default_factory=list)
    image_b64s: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)


async def crawl_all_keywords(
    keywords: list[str] | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    since_id: str | None = None,
) -> list[ParsedPost]:
    """키워드 리스트를 OR 쿼리로 묶어 X API 1회 호출, ParsedPost 리스트 반환

    keywords 미전달 시 DRUG_KEYWORDS 전체 사용.
    max_results: 최대 수집 건수 (기본 100, X API 상한 100)
    since_id: 이 tweet ID보다 큰(최신) 게시글만 수집 — 중복 크롤링 방지
    """
    targets = keywords if keywords is not None else DRUG_KEYWORDS
    query = _build_query(targets)
    posts = await _crawl_query(query, max_results=max_results, since_id=since_id)

    for post in posts:
        post.matched_keywords = _tag_keywords(post.content, targets)

    return posts


async def fetch_tweet_by_url(url: str) -> ParsedPost:
    """트윗 URL로 단건 조회하여 ParsedPost 반환"""
    tweet_id = url.rstrip("/").split("/")[-1]
    params = {
        "tweet.fields": ",".join(TWEET_FIELDS),
        "expansions": ",".join(EXPANSIONS),
        "user.fields": ",".join(USER_FIELDS),
        "media.fields": ",".join(MEDIA_FIELDS),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{X_TWEET_URL}/{tweet_id}",
            headers={"Authorization": f"Bearer {settings.X_BEARER_TOKEN}"},
            params=params,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"X API 오류 {resp.status_code}: {resp.text}")

        data = resp.json()
        tweet = data["data"]
        includes = data.get("includes", {})
        users = {u["id"]: u for u in includes.get("users", [])}
        media_map = {m["media_key"]: m for m in includes.get("media", [])}

        post = _parse_tweet(tweet, users, media_map)
        post.image_b64s = await _download_images(post.image_urls)
        return post


def _build_query(
    keywords: list[str],
    lang: str = "ko",
    exclude_retweets: bool = True,
) -> str:
    """키워드 리스트를 OR 조건으로 묶어 X API 쿼리 문자열 생성

    예: ["브액", "필로폰"] → "(브액 OR 필로폰) lang:ko -is:retweet"
    """
    joined = " OR ".join(keywords)
    query = f"({joined})"
    if lang:
        query += f" lang:{lang}"
    if exclude_retweets:
        query += " -is:retweet"
    return query


def _tag_keywords(content: str, keywords: list[str]) -> list[str]:
    """게시글 본문에서 매칭된 키워드 목록 반환"""
    return [kw for kw in keywords if kw in content]


def _build_params(
    query: str,
    page_size: int = 100,
    next_token: str | None = None,
    since_id: str | None = None,
) -> dict:
    start_time = (
        datetime.now(timezone.utc) - timedelta(hours=CRAWL_WINDOW_HOURS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    params: dict = {
        "query": query,
        "max_results": page_size,
        "start_time": start_time,
        "tweet.fields": ",".join(TWEET_FIELDS),
        "expansions": ",".join(EXPANSIONS),
        "user.fields": ",".join(USER_FIELDS),
        "media.fields": ",".join(MEDIA_FIELDS),
    }
    if next_token:
        params["next_token"] = next_token
    if since_id:
        params["since_id"] = since_id
    return params


async def _crawl_query(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    since_id: str | None = None,
) -> list[ParsedPost]:
    """OR 쿼리로 트윗을 수집하여 ParsedPost 리스트 반환 (페이지네이션 지원)"""
    posts: list[ParsedPost] = []

    page_size = max(min(max_results, _X_MAX_RESULTS_PER_PAGE), _X_MIN_RESULTS_PER_PAGE)

    async with httpx.AsyncClient(timeout=30.0) as client:
        next_token: str | None = None

        while True:
            params = _build_params(
                query, page_size=page_size, next_token=next_token, since_id=since_id
            )

            resp = await client.get(
                X_SEARCH_URL,
                headers={"Authorization": f"Bearer {settings.X_BEARER_TOKEN}"},
                params=params,
            )

            if resp.status_code != 200:
                if resp.status_code in _FATAL_STATUS_CODES:
                    raise RuntimeError(
                        f"X API 치명적 오류 {resp.status_code} — 크롤링 중단"
                    )
                break

            data = resp.json()
            tweets = data.get("data", [])
            if not tweets:
                break

            includes = data.get("includes", {})
            users = {u["id"]: u for u in includes.get("users", [])}
            media_map = {m["media_key"]: m for m in includes.get("media", [])}

            for tweet in tweets:
                post = _parse_tweet(tweet, users, media_map)
                post.image_b64s = await _download_images(post.image_urls)
                posts.append(post)
                if len(posts) >= max_results:
                    break

            if len(posts) >= max_results:
                break

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

    return posts


def _parse_tweet(
    tweet: dict,
    users: dict[str, dict],
    media_map: dict[str, dict],
) -> ParsedPost:
    author = users.get(tweet["author_id"], {})
    username = author.get("username", "")

    return ParsedPost(
        platform=PLATFORM,
        source_id=tweet["id"],
        source_url=f"https://x.com/{username}/status/{tweet['id']}",
        content=tweet["text"],
        created_at_source=datetime.fromisoformat(
            tweet["created_at"].replace("Z", "+00:00")
        ).astimezone(KST),
        author_id=username,
        image_urls=_extract_image_urls(tweet, media_map),
    )


def _extract_image_urls(tweet: dict, media_map: dict[str, dict]) -> list[str]:
    """photo: url / video·gif: preview_image_url"""
    media_keys = tweet.get("attachments", {}).get("media_keys", [])
    urls: list[str] = []

    for mk in media_keys:
        media = media_map.get(mk)
        if not media:
            continue
        url = (
            media.get("url")
            if media["type"] == "photo"
            else media.get("preview_image_url")
        )
        if url:
            urls.append(url)

    return urls


async def _download_images(image_urls: list[str]) -> list[str]:
    """이미지 URL 리스트를 base64 문자열 리스트로 변환"""
    b64s: list[str] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in image_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    b64s.append(base64.b64encode(resp.content).decode())
            except Exception:
                continue
    return b64s
