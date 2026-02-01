"""Построитель URL для запросов к сайту ФССП."""

from src.domain.models import Person
from src.infrastructure.config import FsspUrls


class FsspUrlBuilder:
    """Построитель URL для различных типов запросов к ФССП."""

    def __init__(self, urls_config: FsspUrls):
        """
        Инициализация построителя URL.

        Args:
            urls_config: Конфигурация URL-шаблонов
        """
        self._urls = urls_config

    def build_ip_url(self, ip_number: str) -> str:
        """
        Построить URL для поиска по номеру ИП.

        Args:
            ip_number: Номер исполнительного производства

        Returns:
            Сформированный URL для запроса
        """
        return self._urls.ip.format(ip_number=ip_number)

    def build_person_url(self, person: Person, region_id: int = -1) -> str:
        """
        Построить URL для поиска по данным физического лица.

        Args:
            person: Данные о человеке (ФИО, дата рождения)
            region_id: ID региона для поиска (-1 для всех регионов)

        Returns:
            Сформированный URL для запроса
        """
        return self._urls.person.format(
            last_name=person.last_name,
            first_name=person.first_name,
            patronymic=person.patronymic or "",
            birthday=person.birthday,
            region_id=region_id,
        )

    def build_inn_url(self, inn: str) -> str:
        """
        Построить URL для поиска по ИНН.

        Args:
            inn: ИНН физического или юридического лица

        Returns:
            Сформированный URL для запроса
        """
        return self._urls.inn.format(inn=inn)
