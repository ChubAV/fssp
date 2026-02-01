"""E2E тесты для API."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, Mock

from src.infrastructure.http.app import create_app
from src.infrastructure.config import create_settings
from src.infrastructure.di import build_container


@pytest.fixture
def mock_container():
    """Мок-контейнер с замоканными зависимостями."""
    settings = create_settings()
    container = build_container(settings)
    
    # Мокаем клиент ФССП
    mock_client = AsyncMock()
    mock_client.fetch.return_value = """
    <div class="results-frame">
        <table class="list">
            <tr>
                <td>Тестовый Должник</td>
                <td>123/45/67/89</td>
                <td>DOC123</td>
                <td></td>
                <td></td>
                <td>100000.00</td>
                <td>Тестовый ОСП</td>
                <td>Тестовый пристав</td>
            </tr>
        </table>
    </div>
    """
    
    # Заменяем клиента в сервисе
    container.fssp_service._client = mock_client
    
    return container


@pytest.fixture
async def test_app(mock_container):
    """Тестовое приложение."""
    app = create_app(mock_container.settings)
    app.state.container = mock_container
    
    # Инициализация без TaskManager для упрощения тестов
    yield app


@pytest.mark.asyncio
async def test_healthcheck(test_app):
    """Тест healthcheck endpoint."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/healthcheck")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_search_by_ip(test_app):
    """Тест поиска по номеру ИП."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/ip",
            json={"ip_number": "123/45/67/89"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1


@pytest.mark.asyncio
async def test_search_by_person(test_app):
    """Тест поиска по данным человека."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/person",
            json={
                "last_name": "Иванов",
                "first_name": "Иван",
                "birthday": "16.05.1992",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


@pytest.mark.asyncio
async def test_search_by_inn(test_app):
    """Тест поиска по ИНН."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/inn",
            json={"inn": "1234567890"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
