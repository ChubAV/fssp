"""Сервис для работы с ФССП."""

from src.domain import DebtorCaseList, Inn, IpNumber, Person
from src.domain.errors import FsspUnavailable
from src.domain.protocols import IFsspClient, IFsspParser, IUrlBuilder


class FsspService:
    """Оркестрация запросов к ФССП: формирование URL, получение HTML, парсинг."""

    def __init__(
        self,
        client: IFsspClient,
        parser: IFsspParser,
        url_builder: IUrlBuilder,
    ):
        """
        Инициализация сервиса ФССП.

        Args:
            client: HTTP-клиент для запросов к ФССП
            parser: Парсер HTML результатов
            url_builder: Построитель URL для запросов
        """
        self._client = client
        self._parser = parser
        self._url_builder = url_builder

    async def by_ip(self, ip_number: IpNumber) -> DebtorCaseList:
        """
        Поиск исполнительных производств по номеру ИП.

        Args:
            ip_number: Номер исполнительного производства

        Returns:
            Список найденных дел

        Raises:
            FsspUnavailable: Сервис ФССП недоступен или вернул пустой ответ
        """
        url = self._url_builder.build_ip_url(ip_number.ip)
        return await self._fetch_and_parse(url, "по номеру ИП")

    async def by_person(self, person: Person) -> DebtorCaseList:
        """
        Поиск исполнительных производств по данным физического лица.

        Args:
            person: Данные о человеке (ФИО, дата рождения)

        Returns:
            Список найденных дел

        Raises:
            FsspUnavailable: Сервис ФССП недоступен или вернул пустой ответ
        """
        url = self._url_builder.build_person_url(person)
        return await self._fetch_and_parse(url, "по человеку")

    async def by_inn(self, inn: Inn) -> DebtorCaseList:
        """
        Поиск исполнительных производств по ИНН.

        Args:
            inn: ИНН физического или юридического лица

        Returns:
            Список найденных дел

        Raises:
            FsspUnavailable: Сервис ФССП недоступен или вернул пустой ответ
        """
        url = self._url_builder.build_inn_url(inn.inn)
        return await self._fetch_and_parse(url, "по ИНН")

    async def _fetch_and_parse(self, url: str, context: str) -> DebtorCaseList:
        """
        Общий метод для получения и парсинга результатов.

        Args:
            url: URL для запроса
            context: Контекст запроса (для сообщения об ошибке)

        Returns:
            Список найденных дел

        Raises:
            FsspUnavailable: Сервис ФССП недоступен или вернул пустой ответ
        """
        html = await self._client.fetch(url)
        cases = self._parser.parse_cases(html)
        if not cases:
            raise FsspUnavailable(f"ФССП вернул пустой ответ {context}")
        return DebtorCaseList.from_rows(cases)
