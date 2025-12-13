"""MCP Server для поиска исполнительных производств в ФССП."""
from mcp.server.fastmcp import FastMCP

from src.application.fssp_service import FsspService
from src.domain import Inn, IpNumber, Person
from src.domain.errors import (
    CaptchaError,
    CaptchaLimitExceeded,
    DomainError,
    FsspUnavailable,
    ParsingError,
)


def create_mcp_server(service: FsspService) -> FastMCP:
    """Создает и настраивает MCP server с инструментами для поиска в ФССП."""
    mcp = FastMCP("FSSP Search Server")

    @mcp.tool()
    async def search_by_ip(ip_number: str) -> dict:
        """
        Поиск исполнительных производств по номеру ИП/СД/СВ.

        Args:
            ip_number: Номер исполнительного производства в формате 1234567/12/34/56
                       или 1234567/12/34/56-ИП

        Returns:
            Словарь с результатами поиска, содержащий список исполнительных производств.
            Каждое производство содержит: регион, должник, номер ИП, документ,
            основание окончания (если есть), сумма долга, отдел, пристав.
        """
        try:
            ip = IpNumber(ip=ip_number)
            result = await service.by_ip(ip)
            return {
                "success": True,
                "count": len(result.items),
                "items": [item.model_dump() for item in result.items],
            }
        except DomainError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    @mcp.tool()
    async def search_by_person(
        last_name: str,
        first_name: str,
        birthday: str,
        patronymic: str | None = None,
    ) -> dict:
        """
        Поиск исполнительных производств по ФИО и дате рождения.

        Args:
            last_name: Фамилия
            first_name: Имя
            birthday: Дата рождения в формате DD.MM.YYYY (например, 16.05.1992)
            patronymic: Отчество (опционально)

        Returns:
            Словарь с результатами поиска, содержащий список исполнительных производств.
            Каждое производство содержит: регион, должник, номер ИП, документ,
            основание окончания (если есть), сумма долга, отдел, пристав.
        """
        try:
            person = Person(
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic,
                birthday=birthday,
            )
            result = await service.by_person(person)
            return {
                "success": True,
                "count": len(result.items),
                "items": [item.model_dump() for item in result.items],
            }
        except DomainError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    @mcp.tool()
    async def search_by_inn(inn: str) -> dict:
        """
        Поиск исполнительных производств по ИНН юридического лица.

        Args:
            inn: ИНН (10 цифр для юридических лиц или 12 цифр для физических лиц)

        Returns:
            Словарь с результатами поиска, содержащий список исполнительных производств.
            Каждое производство содержит: регион, должник, номер ИП, документ,
            основание окончания (если есть), сумма долга, отдел, пристав.
        """
        try:
            inn_obj = Inn(inn=inn)
            result = await service.by_inn(inn_obj)
            return {
                "success": True,
                "count": len(result.items),
                "items": [item.model_dump() for item in result.items],
            }
        except DomainError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    return mcp
