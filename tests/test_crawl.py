import os
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("INTERNAL_API_KEY", "test-secret")

from app.main import app

FAKE_ADMIN_IDS = [str(ObjectId()), str(ObjectId())]
VALID_HEADER = {"X-Internal-Key": "test-secret"}
MAX_RESULTS = 100  # 운영 설정: 1시간당 100개


def make_admin_doc(admin_id: str) -> dict:
    return {"_id": ObjectId(admin_id)}


def make_pipeline_result(total: int = 3, saved: int = 2, skipped: int = 1) -> dict:
    return {"total": total, "saved": saved, "skipped": skipped}


async def test_trigger_crawl_success():
    """정상 케이스: 전체 관리자 크롤링 실행 후 결과 반환"""
    admin_docs = [make_admin_doc(aid) for aid in FAKE_ADMIN_IDS]

    with (
        patch("app.api.crawl_api.db") as mock_db,
        patch(
            "app.api.crawl_api.run_crawl_pipeline", new_callable=AsyncMock
        ) as mock_pipeline,
    ):
        mock_db.admins.find.return_value.to_list = AsyncMock(return_value=admin_docs)
        mock_pipeline.return_value = make_pipeline_result()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/crawl/trigger",
                json={"max_results": MAX_RESULTS},
                headers=VALID_HEADER,
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["admins_processed"] == 2
    assert data["total_saved"] == 4  # saved=2 * 관리자 2명
    assert len(data["results"]) == 2
    assert mock_pipeline.call_count == 2


async def test_trigger_crawl_no_admins():
    """관리자가 없는 경우: 빈 결과 반환"""
    with patch("app.api.crawl_api.db") as mock_db:
        mock_db.admins.find.return_value.to_list = AsyncMock(return_value=[])

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/crawl/trigger",
                json={"max_results": MAX_RESULTS},
                headers=VALID_HEADER,
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["admins_processed"] == 0
    assert data["total_saved"] == 0
    assert data["results"] == []


async def test_trigger_crawl_pipeline_error_isolation():
    """한 관리자 파이프라인 실패해도 나머지는 정상 처리"""
    admin_docs = [make_admin_doc(aid) for aid in FAKE_ADMIN_IDS]

    with (
        patch("app.api.crawl_api.db") as mock_db,
        patch(
            "app.api.crawl_api.run_crawl_pipeline", new_callable=AsyncMock
        ) as mock_pipeline,
    ):
        mock_db.admins.find.return_value.to_list = AsyncMock(return_value=admin_docs)
        mock_pipeline.side_effect = [
            Exception("X API 오류"),
            make_pipeline_result(),
        ]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/crawl/trigger",
                json={"max_results": MAX_RESULTS},
                headers=VALID_HEADER,
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["admins_processed"] == 2
    assert data["total_saved"] == 2  # 성공한 관리자 1명의 saved
    assert data["results"][0]["error"] == "X API 오류"
    assert data["results"][1]["error"] is None


async def test_trigger_crawl_invalid_key():
    """인증 키 불일치: 403 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/crawl/trigger",
            json={"max_results": MAX_RESULTS},
            headers={"X-Internal-Key": "wrong-key"},
        )

    assert resp.status_code == 403


async def test_trigger_crawl_missing_key():
    """인증 키 누락: 403 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/crawl/trigger",
            json={"max_results": MAX_RESULTS},
        )

    assert resp.status_code == 403


async def test_trigger_crawl_max_results_too_large():
    """max_results 범위 초과(101): 422 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/crawl/trigger",
            json={"max_results": 101},
            headers=VALID_HEADER,
        )

    assert resp.status_code == 422


async def test_trigger_crawl_max_results_too_small():
    """max_results X API 최솟값 미만(9): 422 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/crawl/trigger",
            json={"max_results": 9},
            headers=VALID_HEADER,
        )

    assert resp.status_code == 422
