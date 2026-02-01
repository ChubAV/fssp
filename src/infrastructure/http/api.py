"""API endpoints для поиска в ФССП."""

from fastapi import APIRouter, Depends

from src.application.fssp_service import FsspService
from src.domain import Inn, IpNumber, Person

from .dependencies import get_fssp_service
from .schemas import HealthcheckResponse
from .schemas.search import (
    DebtorCaseListResponse,
    SearchByInnRequest,
    SearchByIpRequest,
    SearchByPersonRequest,
)

router = APIRouter()


@router.get(
    "/healthcheck",
    description="Проверяет работоспособность сервиса",
    response_model=HealthcheckResponse,
)
def healthcheck():
    """Проверка работоспособности API."""
    return {"status": "ok"}


@router.post(
    "/ip",
    description="Получает данные по номеру ИП из ФССП",
    response_model=DebtorCaseListResponse,
    summary="Поиск по номеру ИП",
)
async def get_fssp_data_by_ip(
    request: SearchByIpRequest,
    service: FsspService = Depends(get_fssp_service),
):
    """
    Поиск исполнительных производств по номеру ИП.

    Args:
        request: Запрос с номером ИП
        service: Сервис для работы с ФССП

    Returns:
        Список найденных исполнительных производств
    """
    # Конвертация DTO -> Domain
    ip_number = IpNumber(ip=request.ip_number)
    # Выполнение запроса
    cases = await service.by_ip(ip_number)
    # Конвертация Domain -> DTO
    return DebtorCaseListResponse.from_domain(cases)


@router.post(
    "/person",
    description="Получает данные по человеку из ФССП",
    response_model=DebtorCaseListResponse,
    summary="Поиск по ФИО и дате рождения",
)
async def get_fssp_data_by_person(
    request: SearchByPersonRequest,
    service: FsspService = Depends(get_fssp_service),
):
    """
    Поиск исполнительных производств по данным физического лица.

    Args:
        request: Запрос с ФИО и датой рождения
        service: Сервис для работы с ФССП

    Returns:
        Список найденных исполнительных производств
    """
    # Конвертация DTO -> Domain
    person = Person(
        last_name=request.last_name,
        first_name=request.first_name,
        patronymic=request.patronymic,
        birthday=request.birthday,
    )
    # Выполнение запроса
    cases = await service.by_person(person)
    # Конвертация Domain -> DTO
    return DebtorCaseListResponse.from_domain(cases)


@router.post(
    "/inn",
    description="Получает данные по ИНН из ФССП",
    response_model=DebtorCaseListResponse,
    summary="Поиск по ИНН",
)
async def get_fssp_data_by_inn(
    request: SearchByInnRequest,
    service: FsspService = Depends(get_fssp_service),
):
    """
    Поиск исполнительных производств по ИНН.

    Args:
        request: Запрос с ИНН
        service: Сервис для работы с ФССП

    Returns:
        Список найденных исполнительных производств
    """
    # Конвертация DTO -> Domain
    inn = Inn(inn=request.inn)
    # Выполнение запроса
    cases = await service.by_inn(inn)
    # Конвертация Domain -> DTO
    return DebtorCaseListResponse.from_domain(cases)
