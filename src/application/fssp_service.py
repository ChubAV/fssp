from src.infrastructure.config import Settings
from src.domain import DebtorCaseList, Inn, IpNumber, Person
from src.domain.errors import FsspUnavailable
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.parser import FsspHtmlParser


class FsspService:
    """Оркестрация запросов к ФССП: формирование URL, получение HTML, парсинг."""

    def __init__(self, settings: Settings, client: FsspClient, parser: FsspHtmlParser):
        self._settings = settings
        self._client = client
        self._parser = parser

    async def by_ip(self, ip_number: IpNumber) -> DebtorCaseList:
        url = self._settings.urls.ip.format(ip_number=ip_number.ip)
        html = await self._client.fetch(url, self._settings)
        cases = self._parser.parse_cases(html)
        if not cases:
            raise FsspUnavailable("ФССП вернул пустой ответ по номеру ИП")
        return DebtorCaseList.from_rows(cases)

    async def by_person(self, person: Person) -> DebtorCaseList:
        url = self._settings.urls.person.format(
            last_name=person.last_name,
            first_name=person.first_name,
            patronymic=person.patronymic or "",
            birthday=person.birthday,
            region_id=-1,
        )
        html = await self._client.fetch(url, self._settings)
        cases = self._parser.parse_cases(html)
        if not cases:
            raise FsspUnavailable("ФССП вернул пустой ответ по человеку")
        return DebtorCaseList.from_rows(cases)

    async def by_inn(self, inn: Inn) -> DebtorCaseList:
        url = self._settings.urls.inn.format(inn=inn.inn)
        html = await self._client.fetch(url, self._settings)
        cases = self._parser.parse_cases(html)
        if not cases:
            raise FsspUnavailable("ФССП вернул пустой ответ по ИНН")
        return DebtorCaseList.from_rows(cases)
