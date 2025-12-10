import logging
from src.app import create_app
from src.config import create_settings
from src.log import setup_logging
import asyncio
from src.schemas import Inn, IpNumber, Person
from src.service import get_fssp_data_by_ip, get_fssp_data_by_person, get_fssp_data_by_inn

def create_fastapi_app():
    settings = create_settings()
    setup_logging(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        log_path=settings.LOG_PATH,
        max_bytes=settings.LOG_FILE_MAX_BYTES,
        backup_count=settings.LOG_FILE_BACKUP_COUNT,
        )
    app = create_app(settings)
    return app


if __name__ == "__main__":
    print('Запусти через just run')
    # settings = create_settings()
    # ip_number = IpNumber(ip='331473/23/23039-ИП')
    # person = Person(last_name='АБУ', first_name='ШАНАБ', patronymic='ТАРИК ЗИАД МУСТАФА', birthday='16.05.1992')
    # person = Person(last_name='Чуб', first_name='Александр', patronymic='Викторович', birthday='10.05.1984')
    # inn = Inn(inn='2318027030')
    # result = asyncio.run(get_fssp_data_by_ip(ip_number, settings))
    # print(result)
    # result = asyncio.run(get_fssp_data_by_person(person, settings))
    # print(result)
    # result = asyncio.run(get_fssp_data_by_inn(inn, settings))
    # print(result)
