import logging

from src.infrastructure.config import create_settings
from src.infrastructure.http import create_app as create_http_app
from src.infrastructure.logging import setup_logging


def create_fastapi_app():
    settings = create_settings()
    setup_logging(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        log_path=settings.LOG_PATH,
        max_bytes=settings.LOG_FILE_MAX_BYTES,
        backup_count=settings.LOG_FILE_BACKUP_COUNT,
        )
    app = create_http_app(settings)
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
