from unittest.mock import AsyncMock, patch

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.keywords import DEFAULT_KEYWORDS
from app.core.security import get_current_admin
from app.main import app
from app.schemas.crawl_settings import CrawlSettingsOut

FAKE_ADMIN_ID = str(ObjectId())
AUTH_HEADER = {"Authorization": "Bearer token"}


def mock_admin():
    return FAKE_ADMIN_ID


def make_settings_out(**kwargs) -> CrawlSettingsOut:
    return CrawlSettingsOut(
        keywords=kwargs.get("keywords", DEFAULT_KEYWORDS),
        max_results=kwargs.get("max_results", 100),
        crawl_enabled=kwargs.get("crawl_enabled", False),
    )


async def test_get_crawl_settings_default():
    """설정 없는 관리자 조회 시 기본값 반환"""
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.crawl_settings_api.crawl_settings_service") as mock_svc:
        mock_svc.get_settings = AsyncMock(return_value=make_settings_out())

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/crawl-settings", headers=AUTH_HEADER)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["keywords"] == DEFAULT_KEYWORDS
    assert data["max_results"] == 100
    assert data["crawl_enabled"] is False


async def test_get_crawl_settings_custom():
    """저장된 설정 조회"""
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.crawl_settings_api.crawl_settings_service") as mock_svc:
        mock_svc.get_settings = AsyncMock(
            return_value=make_settings_out(
                keywords=["필로폰", "작대기"],
                max_results=50,
                crawl_enabled=True,
            )
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/crawl-settings", headers=AUTH_HEADER)

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["keywords"] == ["필로폰", "작대기"]
    assert data["max_results"] == 50
    assert data["crawl_enabled"] is True


async def test_update_crawl_settings_keywords():
    """키워드 수정"""
    app.dependency_overrides[get_current_admin] = mock_admin

    new_keywords = ["필로폰", "브액", "아이스"]

    with patch("app.api.crawl_settings_api.crawl_settings_service") as mock_svc:
        mock_svc.update_settings = AsyncMock(
            return_value=make_settings_out(keywords=new_keywords)
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/crawl-settings",
                json={"keywords": new_keywords},
                headers=AUTH_HEADER,
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["keywords"] == new_keywords


async def test_update_crawl_settings_max_results():
    """max_results 수정"""
    app.dependency_overrides[get_current_admin] = mock_admin

    with patch("app.api.crawl_settings_api.crawl_settings_service") as mock_svc:
        mock_svc.update_settings = AsyncMock(
            return_value=make_settings_out(max_results=50)
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/crawl-settings",
                json={"max_results": 50},
                headers=AUTH_HEADER,
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["max_results"] == 50


async def test_update_crawl_settings_max_results_too_small():
    """max_results X API 최솟값 미만(9): 422 반환"""
    app.dependency_overrides[get_current_admin] = mock_admin

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.patch(
            "/crawl-settings",
            json={"max_results": 9},
            headers=AUTH_HEADER,
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


async def test_update_crawl_settings_max_results_too_large():
    """max_results 범위 초과(101): 422 반환"""
    app.dependency_overrides[get_current_admin] = mock_admin

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.patch(
            "/crawl-settings",
            json={"max_results": 101},
            headers=AUTH_HEADER,
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


async def test_update_crawl_settings_keywords_with_custom():
    """기본 11개 + 커스텀 2개 = 13개 정상 저장"""
    app.dependency_overrides[get_current_admin] = mock_admin

    full_keywords = DEFAULT_KEYWORDS + ["떨", "케타민"]

    with patch("app.api.crawl_settings_api.crawl_settings_service") as mock_svc:
        mock_svc.update_settings = AsyncMock(
            return_value=make_settings_out(keywords=full_keywords)
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/crawl-settings",
                json={"keywords": full_keywords},
                headers=AUTH_HEADER,
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert len(resp.json()["keywords"]) == 13


async def test_update_crawl_settings_keywords_exceeded():
    """키워드 14개 초과: 422 반환"""
    app.dependency_overrides[get_current_admin] = mock_admin

    too_many = DEFAULT_KEYWORDS + ["떨", "케타민", "헤로인"]  # 14개

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.patch(
            "/crawl-settings",
            json={"keywords": too_many},
            headers=AUTH_HEADER,
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


async def test_get_crawl_settings_unauthorized():
    """인증 없이 조회: 401 반환"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/crawl-settings")

    assert resp.status_code == 401
