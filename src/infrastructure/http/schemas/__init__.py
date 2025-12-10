"""HTTP-специфичные схемы для API."""
from pydantic import BaseModel, RootModel


class DebItem(BaseModel):
    """DTO элемента результата для API."""

    region: str | None = None
    debtor: str
    ip: str
    doc: str
    end_reason: str | None = None
    debt: str
    office: str
    bailiff: str


class DebItemList(RootModel[list[DebItem]]):
    """Список элементов ИП в API-ответе."""

    root: list[DebItem]


class ErrorResponse(BaseModel):
    """Общий формат ошибки API."""

    detail: str


class HealthcheckResponse(BaseModel):
    """Ответ на запрос healthcheck"""

    status: str
