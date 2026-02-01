"""Unit-тесты для FsspHtmlParser."""

import pytest

from src.infrastructure.parser import FsspHtmlParser
from src.domain.errors import CaptchaLimitExceeded, ParsingError


@pytest.fixture
def parser():
    """Создать парсер."""
    return FsspHtmlParser()


def test_parse_cases_success(parser, sample_html_result):
    """Тест успешного парсинга результатов."""
    # Act
    cases = parser.parse_cases(sample_html_result)

    # Assert
    assert len(cases) == 1
    assert cases[0]["debtor"] == "Иванов Иван Иванович"
    assert cases[0]["ip"] == "1234567/12/34/56"
    assert cases[0]["region"] == "Московская область"
    assert cases[0]["debt"] == "100000.00"


def test_parse_cases_empty_table(parser):
    """Тест парсинга пустой таблицы."""
    # Arrange
    html = '<div class="results"><div>Нет результатов</div></div>'

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert cases == []


def test_parse_cases_captcha_limit_exceeded(parser):
    """Тест обработки превышения лимита капчи."""
    # Arrange
    html = '''
    <div class="results">
        <div class="empty">Количество неверных попыток ввода кода превышено</div>
    </div>
    '''

    # Act & Assert
    with pytest.raises(CaptchaLimitExceeded, match="Превышено количество"):
        parser.parse_cases(html)


def test_parse_cases_multiple_rows(parser):
    """Тест парсинга нескольких строк."""
    # Arrange
    html = """
    <div class="results-frame">
        <table class="list">
            <tr class="region-title">Москва</tr>
            <tr>
                <td>Должник 1</td>
                <td>111/11/11/11</td>
                <td>DOC1</td>
                <td></td>
                <td></td>
                <td>1000</td>
                <td>ОСП 1</td>
                <td>Пристав 1</td>
            </tr>
            <tr>
                <td>Должник 2</td>
                <td>222/22/22/22</td>
                <td>DOC2</td>
                <td></td>
                <td></td>
                <td>2000</td>
                <td>ОСП 2</td>
                <td>Пристав 2</td>
            </tr>
        </table>
    </div>
    """

    # Act
    cases = parser.parse_cases(html)

    # Assert
    assert len(cases) == 2
    assert cases[0]["debtor"] == "Должник 1"
    assert cases[1]["debtor"] == "Должник 2"
    assert all(case["region"] == "Москва" for case in cases)
