"""Unit-тесты для FsspUrlBuilder."""

import pytest

from src.infrastructure.url_builder import FsspUrlBuilder
from src.infrastructure.config import FsspUrls
from src.domain.models import Person


@pytest.fixture
def url_builder():
    """Создать построитель URL."""
    urls = FsspUrls()
    return FsspUrlBuilder(urls)


def test_build_ip_url(url_builder):
    """Тест построения URL для поиска по ИП."""
    # Act
    url = url_builder.build_ip_url("1234567/12/34/56")

    # Assert
    assert "1234567/12/34/56" in url
    assert "variant" in url
    assert "ip_number" in url


def test_build_person_url(url_builder):
    """Тест построения URL для поиска по человеку."""
    # Arrange
    person = Person(
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        birthday="16.05.1992",
    )

    # Act
    url = url_builder.build_person_url(person)

    # Assert
    assert "Иванов" in url
    assert "Иван" in url
    assert "Иванович" in url
    assert "16.05.1992" in url
    assert "region_id" in url


def test_build_person_url_without_patronymic(url_builder):
    """Тест построения URL для поиска по человеку без отчества."""
    # Arrange
    person = Person(
        last_name="Смит",
        first_name="Джон",
        patronymic=None,
        birthday="01.01.1990",
    )

    # Act
    url = url_builder.build_person_url(person)

    # Assert
    assert "Смит" in url
    assert "Джон" in url
    assert "01.01.1990" in url


def test_build_inn_url(url_builder):
    """Тест построения URL для поиска по ИНН."""
    # Act
    url = url_builder.build_inn_url("1234567890")

    # Assert
    assert "1234567890" in url
    assert "inn" in url
    assert "variant" in url


def test_build_person_url_custom_region(url_builder):
    """Тест построения URL с нестандартным регионом."""
    # Arrange
    person = Person(
        last_name="Петров",
        first_name="Петр",
        birthday="10.10.1980",
    )

    # Act
    url = url_builder.build_person_url(person, region_id=77)

    # Assert
    assert "region_id%5D%5B0%5D=77" in url or "region_id[0]=77" in url
