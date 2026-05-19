from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def mock_db():
    with patch("app.api.health_api.db") as db:
        db.command = AsyncMock()
        yield db


async def test_health_check_success(mock_db):
    mock_db.command.return_value = {"ok": 1}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "MongoDB connected"}


async def test_health_check_failure(mock_db):
    from pymongo.errors import PyMongoError

    mock_db.command.side_effect = PyMongoError("connection failed")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "MongoDB failed"}
