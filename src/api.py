from fastapi import APIRouter, Depends
from src.config import Settings
from src.dependencies import get_settings
from src.schemas import DebItemList, HealthcheckResponse, Inn, IpNumber, Person
from src.service import get_fssp_data_by_ip as get_fssp_data_by_ip_service
from src.service import get_fssp_data_by_person as get_fssp_data_by_person_service
from src.service import get_fssp_data_by_inn as get_fssp_data_by_inn_service

router = APIRouter()

@router.get("/healthcheck", description="Проверяет работоспособность сервиса", response_model=HealthcheckResponse)
def healthcheck():
    return {"status": "ok"}

@router.post("/ip", description="Получает данные по номеру ИП из ФССП", response_model=DebItemList)
async def get_fssp_data_by_ip(ip_number: IpNumber, settings: Settings = Depends(get_settings)):
    return await get_fssp_data_by_ip_service(ip_number, settings)

@router.post("/person", description="Получает данные по человеку из ФССП", response_model=DebItemList)
async def get_fssp_data_by_person(person: Person, settings: Settings = Depends(get_settings)):
    return await get_fssp_data_by_person_service(person, settings)

@router.post("/inn", description="Получает данные по ИНН (юридического лица) из ФССП", response_model=DebItemList)
async def get_fssp_data_by_inn(inn: Inn, settings: Settings = Depends(get_settings)):
    return await get_fssp_data_by_inn_service(inn, settings)