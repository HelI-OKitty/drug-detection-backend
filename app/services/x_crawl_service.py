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

X_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
PLATFORM = "x"
CRAWL_DAYS = 3  # 테스트 기간, 이후 조정


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
    image_b64s: list[str] = field(default_factory=list)  # 다운로드된 이미지 base64


async def crawl_keyword(keyword: str) -> list[ParsedPost]:
    """키워드로 최근 CRAWL_DAYS일치 트윗을 수집하여 ParsedPost 리스트로 반환"""
    start_time = (datetime.now(timezone.utc) - timedelta(days=CRAWL_DAYS)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    posts: list[ParsedPost] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        next_token: str | None = None

        while True:
            params: dict = {
                "query": f"{keyword} -is:retweet lang:ko",
                "max_results": 100,
                "start_time": start_time,
                "tweet.fields": "created_at,author_id,attachments,entities",
                "expansions": "author_id,attachments.media_keys",
                "user.fields": "username",
                "media.fields": "url,type,preview_image_url",
            }
            if next_token:
                params["pagination_token"] = next_token

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
                post = _parse_tweet(tweet, users, media_map)
                posts.append(post)

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

    # 이미지 다운로드 (각 post의 image_urls → base64)
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

    source_url = f"https://x.com/{username}/status/{tweet['id']}"

    image_urls = _extract_image_urls(tweet, media_map)

    return ParsedPost(
        platform=PLATFORM,
        source_id=tweet["id"],
        source_url=source_url,
        content=tweet["text"],
        created_at_source=datetime.fromisoformat(
            tweet["created_at"].replace("Z", "+00:00")
        ),
        author_name=username,
        image_urls=image_urls,
    )


def _extract_image_urls(tweet: dict, media_map: dict[str, dict]) -> list[str]:
    """트윗에 첨부된 미디어 URL 추출 — photo: url, video/gif: preview_image_url"""
    media_keys = tweet.get("attachments", {}).get("media_keys", [])
    urls: list[str] = []

    for mk in media_keys:
        media = media_map.get(mk)
        if not media:
            continue
        if media["type"] == "photo":
            url = media.get("url")
        else:
            # video, animated_gif → 썸네일
            url = media.get("preview_image_url")
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
