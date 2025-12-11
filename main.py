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
   print('Используй just')