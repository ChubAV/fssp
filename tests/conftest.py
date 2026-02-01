"""Общие фикстуры для тестов."""

import pytest
from unittest.mock import AsyncMock, Mock

from src.domain.models import Person, IpNumber, Inn


@pytest.fixture
def sample_person():
    """Тестовые данные человека."""
    return Person(
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        birthday="16.05.1992",
    )


@pytest.fixture
def sample_ip_number():
    """Тестовый номер ИП."""
    return IpNumber(ip="1234567/12/34/56")


@pytest.fixture
def sample_inn():
    """Тестовый ИНН."""
    return Inn(inn="1234567890")


@pytest.fixture
def sample_html_result():
    """Пример HTML результата от ФССП."""
    return """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Московская область</tr>
            <tr>
                <td>Иванов Иван Иванович</td>
                <td>1234567/12/34/56</td>
                <td>123456</td>
                <td></td>
                <td></td>
                <td>100000.00</td>
                <td>ОСП по Одинцовскому району</td>
                <td>Петров П.П.</td>
            </tr>
        </table>
    </div>
    """


@pytest.fixture
def sample_parsed_cases():
    """Пример распарсенных дел."""
    return [
        {
            "region": "Московская область",
            "debtor": "Иванов Иван Иванович",
            "ip": "1234567/12/34/56",
            "doc": "123456",
            "end_reason": "",
            "debt": "100000.00",
            "office": "ОСП по Одинцовскому району",
            "bailiff": "Петров П.П.",
        }
    ]


@pytest.fixture
def mock_fssp_client():
    """Мок HTTP-клиента ФССП."""
    client = AsyncMock()
    client.fetch.return_value = "<html>mock result</html>"
    return client


@pytest.fixture
def mock_parser():
    """Мок парсера HTML."""
    parser = Mock()
    parser.parse_cases.return_value = [
        {
            "region": "Москва",
            "debtor": "Тестовый Должник",
            "ip": "123/45/67/89",
            "doc": "12345",
            "end_reason": "",
            "debt": "50000.00",
            "office": "Тестовый отдел",
            "bailiff": "Тестовый пристав",
        }
    ]
    return parser


@pytest.fixture
def mock_url_builder():
    """Мок построителя URL."""
    builder = Mock()
    builder.build_ip_url.return_value = "http://fssp.gov.ru/ip/test"
    builder.build_person_url.return_value = "http://fssp.gov.ru/person/test"
    builder.build_inn_url.return_value = "http://fssp.gov.ru/inn/test"
    return builder


@pytest.fixture
def mock_task_repository():
    """Мок репозитория задач."""
    repo = AsyncMock()
    return repo
