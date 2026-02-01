"""Unit-тесты для доменных моделей."""

import pytest
from pydantic import ValidationError

from src.domain.models import Person, Inn, IpNumber, DebtorCase, DebtorCaseList


def test_person_valid():
    """Тест валидной модели Person."""
    person = Person(
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        birthday="16.05.1992",
    )
    assert person.last_name == "Иванов"
    assert person.first_name == "Иван"
    assert person.patronymic == "Иванович"
    assert person.birthday == "16.05.1992"


def test_person_without_patronymic():
    """Тест модели Person без отчества."""
    person = Person(
        last_name="Смит",
        first_name="Джон",
        birthday="01.01.1990",
    )
    assert person.patronymic is None


def test_person_invalid_birthday():
    """Тест невалидной даты рождения."""
    with pytest.raises(ValidationError):
        Person(
            last_name="Иванов",
            first_name="Иван",
            birthday="invalid-date",
        )


def test_person_future_birthday():
    """Тест даты рождения в будущем."""
    with pytest.raises(ValidationError):
        Person(
            last_name="Иванов",
            first_name="Иван",
            birthday="01.01.2030",
        )


def test_inn_valid_10_digits():
    """Тест валидного ИНН юрлица (10 цифр)."""
    inn = Inn(inn="1234567890")
    assert inn.inn == "1234567890"


def test_inn_valid_12_digits():
    """Тест валидного ИНН физлица (12 цифр)."""
    inn = Inn(inn="123456789012")
    assert inn.inn == "123456789012"


def test_inn_invalid():
    """Тест невалидного ИНН."""
    with pytest.raises(ValidationError):
        Inn(inn="12345")


def test_ip_number_valid():
    """Тест валидного номера ИП."""
    ip = IpNumber(ip="1234567/12/34/56")
    assert ip.ip == "1234567/12/34/56"


def test_ip_number_with_suffix():
    """Тест номера ИП с кириллическим суффиксом."""
    ip = IpNumber(ip="1234567/12/34567-ИП")
    assert ip.ip == "1234567/12/34567-ИП"


def test_ip_number_invalid():
    """Тест невалидного номера ИП."""
    with pytest.raises(ValidationError):
        IpNumber(ip="invalid")


def test_debtor_case():
    """Тест модели DebtorCase."""
    case = DebtorCase(
        region="Москва",
        debtor="Иванов И.И.",
        ip="123/45/67/89",
        doc="DOC123",
        end_reason=None,
        debt="100000.00",
        office="ОСП Москва",
        bailiff="Петров П.П.",
    )
    assert case.debtor == "Иванов И.И."
    assert case.region == "Москва"


def test_debtor_case_list_from_rows():
    """Тест создания DebtorCaseList из списка словарей."""
    rows = [
        {
            "debtor": "Должник 1",
            "ip": "111/11/11/11",
            "doc": "DOC1",
            "debt": "1000",
            "office": "ОСП 1",
            "bailiff": "Пристав 1",
        },
        {
            "debtor": "Должник 2",
            "ip": "222/22/22/22",
            "doc": "DOC2",
            "debt": "2000",
            "office": "ОСП 2",
            "bailiff": "Пристав 2",
        },
    ]

    case_list = DebtorCaseList.from_rows(rows)
    assert len(case_list.items) == 2
    assert case_list.items[0].debtor == "Должник 1"
    assert case_list.items[1].debtor == "Должник 2"
