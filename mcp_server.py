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
        log_path=settings.LOG_PATH,
        max_bytes=settings.LOG_FILE_MAX_BYTES,
        backup_count=settings.LOG_FILE_BACKUP_COUNT,
    )

    # Проверка наличия API ключа для капчи
    if settings.captcha is None or not settings.captcha.api_key:
        print(
            "Ошибка: Не задан API ключ RuCaptcha (RUCAPTCH_API_KEY)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Инициализация зависимостей
    solver = CaptchaSolver(settings.captcha.api_key)
    client = FsspClient(solver)
    parser = FsspHtmlParser()
    service = FsspService(settings, client, parser)

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
