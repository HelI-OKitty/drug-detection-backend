"""
X 크롤링 단독 테스트 스크립트

사용법:
    python scripts/test_crawl.py              # 전체 키워드, crawling_data/ 자동 저장
    python scripts/test_crawl.py --keyword 브액 필로폰   # 키워드 직접 지정
    python scripts/test_crawl.py --max-results 50       # 최대 수집 건수 지정
    python scripts/test_crawl.py --url https://x.com/user/status/123
    python scripts/test_crawl.py --out path/to/result.json  # 경로 직접 지정
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.x_crawl_service import (
    DEFAULT_MAX_RESULTS,
    ParsedPost,
    crawl_all_keywords,
    fetch_tweet_by_url,
)


def post_to_dict(post: ParsedPost) -> dict:
    return {
        "platform": post.platform,
        "source_id": post.source_id,
        "source_url": post.source_url,
        "content": post.content,
        "created_at_source": post.created_at_source.isoformat(),
        "author_id": post.author_id,
        "matched_keywords": post.matched_keywords,
        "image_urls": post.image_urls,
        "image_b64s_count": len(post.image_b64s),
    }


async def run(
    keywords: list[str] | None,
    out_path: str | None,
    max_results: int = DEFAULT_MAX_RESULTS,
    url: str | None = None,
) -> None:
    print("크롤링 시작...", flush=True)

    if url:
        post = await fetch_tweet_by_url(url)
        results = [post_to_dict(post)]
    else:
        posts = await crawl_all_keywords(keywords, max_results=max_results)
        results = [post_to_dict(p) for p in posts]

    print(f"\n총 {len(results)}건 수집 완료")

    if out_path:
        path = Path(out_path)
    else:
        crawling_dir = Path(__file__).resolve().parent.parent / "crawling_data"
        crawling_dir.mkdir(exist_ok=True)
        n = 1
        while (crawling_dir / f"crawling_result{n}.json").exists():
            n += 1
        path = crawling_dir / f"crawling_result{n}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"저장 완료: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="X 크롤링 단독 테스트")
    parser.add_argument(
        "--keyword",
        nargs="+",
        help="테스트할 키워드 (여러 개 가능, 미입력 시 DRUG_KEYWORDS 전체 사용)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"최대 수집 건수 (기본값: {DEFAULT_MAX_RESULTS})",
    )
    parser.add_argument(
        "--out",
        help="결과 저장 경로 (미입력 시 crawling_data/ 에 번호 순으로 자동 저장)",
    )
    parser.add_argument(
        "--url",
        help="트윗 URL 단건 조회 (입력 시 --keyword, --max-results 무시)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(args.keyword, args.out, args.max_results, args.url))
