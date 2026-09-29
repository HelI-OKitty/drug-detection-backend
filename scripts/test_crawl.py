"""
X 크롤링 단독 테스트 스크립트

사용법:
    python scripts/test_crawl.py                      # DRUG_KEYWORDS 전체
    python scripts/test_crawl.py --keyword 작대기      # 단일 키워드
    python scripts/test_crawl.py --keyword 작대기 --out result.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.keywords import DRUG_KEYWORDS
from app.services.x_crawl_service import ParsedPost, crawl_keyword


def post_to_dict(post: ParsedPost) -> dict:
    return {
        "platform": post.platform,
        "source_id": post.source_id,
        "source_url": post.source_url,
        "content": post.content,
        "created_at_source": post.created_at_source.isoformat(),
        "author_name": post.author_name,
        "image_urls": post.image_urls,
        "image_b64s_count": len(post.image_b64s),  # base64는 길어서 개수만 출력
    }


async def run(keywords: list[str], out_path: str | None) -> None:
    results: dict[str, list[dict]] = {}

    for keyword in keywords:
        print(f"[{keyword}] 크롤링 중...", flush=True)
        posts = await crawl_keyword(keyword)
        results[keyword] = [post_to_dict(p) for p in posts]
        print(f"[{keyword}] {len(posts)}건 수집", flush=True)

    total = sum(len(v) for v in results.values())
    print(f"\n총 {total}건 수집 완료")

    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"저장 완료: {path}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="X 크롤링 단독 테스트")
    parser.add_argument(
        "--keyword",
        help="테스트할 키워드 (미입력 시 DRUG_KEYWORDS 전체 사용)",
    )
    parser.add_argument(
        "--out",
        help="결과 저장 경로 (미입력 시 stdout 출력)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    keywords = [args.keyword] if args.keyword else DRUG_KEYWORDS
    asyncio.run(run(keywords, args.out))
