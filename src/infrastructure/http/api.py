from fastapi import APIRouter, Depends

from src.application.fssp_service import FsspService
from src.domain import Inn, IpNumber, Person

from .dependencies import get_fssp_service
from .schemas import DebItemList, HealthcheckResponse

router = APIRouter()


@router.get("/healthcheck", description="Проверяет работоспособность сервиса", response_model=HealthcheckResponse)
def healthcheck():
    return {"status": "ok"}


@router.post("/ip", description="Получает данные по номеру ИП из ФССП", response_model=DebItemList)
async def get_fssp_data_by_ip(ip_number: IpNumber, service: FsspService = Depends(get_fssp_service)):
    cases = await service.by_ip(ip_number)
    return DebItemList(root=[case.model_dump() for case in cases.items])


@router.post("/person", description="Получает данные по человеку из ФССП", response_model=DebItemList)
async def get_fssp_data_by_person(person: Person, service: FsspService = Depends(get_fssp_service)):
    cases = await service.by_person(person)
    return DebItemList(root=[case.model_dump() for case in cases.items])


@router.post("/inn", description="Получает данные по ИНН (юридического лица) из ФССП", response_model=DebItemList)
async def get_fssp_data_by_inn(inn: Inn, service: FsspService = Depends(get_fssp_service)):
    cases = await service.by_inn(inn)
    return DebItemList(root=[case.model_dump() for case in cases.items])
