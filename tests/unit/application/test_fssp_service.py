"""Unit-тесты для FsspService."""

import pytest

from src.application.fssp_service import FsspService
from src.domain.errors import FsspUnavailable


@pytest.fixture
def fssp_service(mock_fssp_client, mock_parser, mock_url_builder):
    """Создать FsspService с моками."""
    return FsspService(
        client=mock_fssp_client,
        parser=mock_parser,
        url_builder=mock_url_builder,
    )


@pytest.mark.asyncio
async def test_by_ip_success(fssp_service, sample_ip_number, mock_fssp_client, mock_parser, mock_url_builder):
    """Тест успешного поиска по номеру ИП."""
    # Arrange
    mock_fssp_client.fetch.return_value = "<html>result</html>"
    mock_parser.parse_cases.return_value = [{"debtor": "Тест", "ip": "123", "doc": "456", "debt": "1000", "office": "ОСП", "bailiff": "Иванов"}]

    # Act
    result = await fssp_service.by_ip(sample_ip_number)

    # Assert
    assert len(result.items) == 1
    assert result.items[0].debtor == "Тест"
    mock_url_builder.build_ip_url.assert_called_once_with(sample_ip_number.ip)
    mock_fssp_client.fetch.assert_called_once()
    mock_parser.parse_cases.assert_called_once_with("<html>result</html>")


@pytest.mark.asyncio
async def test_by_ip_empty_result(fssp_service, sample_ip_number, mock_parser):
    """Тест обработки пустого ответа при поиске по ИП."""
    # Arrange
    mock_parser.parse_cases.return_value = []

    # Act & Assert
    with pytest.raises(FsspUnavailable, match="пустой ответ по номеру ИП"):
        await fssp_service.by_ip(sample_ip_number)


@pytest.mark.asyncio
async def test_by_person_success(fssp_service, sample_person, mock_fssp_client, mock_parser):
    """Тест успешного поиска по данным человека."""
    # Arrange
    mock_fssp_client.fetch.return_value = "<html>result</html>"

    # Act
    result = await fssp_service.by_person(sample_person)

    # Assert
    assert len(result.items) == 1
    mock_fssp_client.fetch.assert_called_once()
    mock_parser.parse_cases.assert_called_once()


@pytest.mark.asyncio
async def test_by_inn_success(fssp_service, sample_inn, mock_fssp_client, mock_parser):
    """Тест успешного поиска по ИНН."""
    # Arrange
    mock_fssp_client.fetch.return_value = "<html>result</html>"

    # Act
    result = await fssp_service.by_inn(sample_inn)

    # Assert
    assert len(result.items) == 1
    mock_fssp_client.fetch.assert_called_once()
    mock_parser.parse_cases.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_and_parse_integration(fssp_service, mock_fssp_client, mock_parser, mock_url_builder):
    """Тест интеграции fetch и parse через _fetch_and_parse."""
    # Arrange
    test_url = "http://test.url"
    mock_fssp_client.fetch.return_value = "<html>test</html>"
    mock_parser.parse_cases.return_value = [{"debtor": "Test", "ip": "1", "doc": "2", "debt": "100", "office": "OSP", "bailiff": "Officer"}]

    # Act
    result = await fssp_service._fetch_and_parse(test_url, "тестовый контекст")

    # Assert
    assert len(result.items) == 1
    mock_fssp_client.fetch.assert_called_once_with(test_url)
    mock_parser.parse_cases.assert_called_once_with("<html>test</html>")
