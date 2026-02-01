"""Точка входа для MCP Server поиска исполнительных производств в ФССП."""
import logging
import sys

from src.infrastructure.config import create_settings
from src.infrastructure.logging import setup_logging
from src.infrastructure.captcha import CaptchaSolver
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.parser import FsspHtmlParser
from src.application.fssp_service import FsspService
from src.infrastructure.mcp.server import create_mcp_server


def main():
    """Инициализация и запуск MCP server."""
    settings = create_settings()
    
    # Настройка логирования
    setup_logging(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        log_path=settings.log_path,
        max_bytes=settings.LOG_FILE_MAX_BYTES,
        backup_count=settings.LOG_FILE_BACKUP_COUNT,
    )

    # Проверка наличия API ключа для капчи
    if not settings.RUCAPTCH_API_KEY:
        print(
            "Ошибка: Не задан API ключ RuCaptcha (RUCAPTCH_API_KEY)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Инициализация зависимостей через DI контейнер
    from src.infrastructure.di import build_container
    container = build_container(settings)
    service = container.fssp_service

    # Создание MCP server
    mcp = create_mcp_server(service)

    # Определение транспорта
    transport = settings.MCP_TRANSPORT.lower()
    
    if transport == "http":
        # Запуск через HTTP транспорт
        import uvicorn
        
        app = mcp.http_app()
        host = settings.MCP_HOST
        port = settings.MCP_PORT
        
        print(f"Запуск MCP server через HTTP на {host}:{port}", file=sys.stderr)
        uvicorn.run(app, host=host, port=port)
    else:
        # Запуск через stdio (стандартный режим)
        print("Запуск MCP server через stdio", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
