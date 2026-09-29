"""
X(트위터) API v2 크롤링 서비스

흐름:
  키워드 검색 → 트윗 파싱 → 이미지 다운로드(base64) → ParsedPost 반환
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings
from app.core.keywords import DRUG_KEYWORDS

X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
PLATFORM = "x"
CRAWL_DAYS = 3  # 테스트 기간, 이후 조정

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
    author_name: str
    image_urls: list[str] = field(default_factory=list)
    image_b64s: list[str] = field(default_factory=list)


async def crawl_all_keywords(
    keywords: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, list[ParsedPost]]:
    """키워드 목록을 순차적으로 크롤링하여 키워드별 결과를 반환

    keywords 미전달 시 DRUG_KEYWORDS 전체 사용.
    limit: 키워드당 최대 수집 건수 (None이면 전체 수집)
    추후 키워드별 개별 주기 스케줄링 시 keywords 인자로 제어 가능.
    """
    targets = keywords if keywords is not None else DRUG_KEYWORDS
    results: dict[str, list[ParsedPost]] = {}

    for keyword in targets:
        results[keyword] = await crawl_keyword(keyword, limit=limit)

    return results


def _build_query(keyword: str, lang: str = "ko", exclude_retweets: bool = True) -> str:
    query = keyword
    if lang:
        query += f" lang:{lang}"
    if exclude_retweets:
        query += " -is:retweet"
    return query


def _build_params(query: str, next_token: str | None = None) -> dict:
    start_time = (datetime.now(timezone.utc) - timedelta(days=CRAWL_DAYS)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    params: dict = {
        "query": query,
        "max_results": 100,
        "start_time": start_time,
        "tweet.fields": ",".join(TWEET_FIELDS),
        "expansions": ",".join(EXPANSIONS),
        "user.fields": ",".join(USER_FIELDS),
        "media.fields": ",".join(MEDIA_FIELDS),
    }
    if next_token:
        params["next_token"] = next_token
    return params


async def crawl_keyword(
    keyword: str,
    limit: int | None = None,
) -> list[ParsedPost]:
    """키워드로 최근 CRAWL_DAYS일치 트윗을 수집하여 ParsedPost 리스트로 반환

    limit: 최대 수집 건수 (None이면 전체 수집)
    """
    query = _build_query(keyword)
    posts: list[ParsedPost] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        next_token: str | None = None

        while True:
            params = _build_params(query, next_token=next_token)

            resp = await client.get(
                X_SEARCH_URL,
                headers={"Authorization": f"Bearer {settings.X_BEARER_TOKEN}"},
                params=params,
            )

            if resp.status_code != 200:
                break

            data = resp.json()
            tweets = data.get("data", [])
            if not tweets:
                break

            includes = data.get("includes", {})
            users = {u["id"]: u for u in includes.get("users", [])}
            media_map = {m["media_key"]: m for m in includes.get("media", [])}

            for tweet in tweets:
                posts.append(_parse_tweet(tweet, users, media_map))
                if limit and len(posts) >= limit:
                    break

            if limit and len(posts) >= limit:
                break

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

    for post in posts:
        post.image_b64s = await _download_images(post.image_urls)

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
        ),
        author_name=username,
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
    async with httpx.AsyncClient(timeout=15.0) as client:
        for url in image_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    b64s.append(base64.b64encode(resp.content).decode())
            except httpx.HTTPError:
                continue
    return b64s
