"""FastAPI приложение."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.errors import CaptchaLimitExceeded, DomainError
from src.infrastructure.config import Settings
from src.infrastructure.di import Container, build_container

from .api import router as api_router
from .middleware import add_request_context
from .tasks_api import router as tasks_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    container: Container = app.state.container

    # Инициализация репозитория задач
    await container.task_repository.initialize()
    logger.info("Task repository инициализирован", db_path=str(container.settings.database_path))

    # Запуск TaskManager
    await container.task_manager.start()
    logger.info("Task manager запущен")

    yield

    # Остановка TaskManager
    await container.task_manager.stop()
    logger.info("Task manager остановлен")

    # Закрытие репозитория
    await container.task_repository.close()
    logger.info("Task repository закрыт")


def create_app(settings: Settings):
    """
    Создать и настроить FastAPI приложение.

    Args:
        settings: Настройки приложения

    Returns:
        Настроенное FastAPI приложение
    """
    # Построение контейнера зависимостей
    container = build_container(settings)

    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
    app.middleware("http")(add_request_context)
    
    # Сохраняем контейнер в состоянии приложения
    app.state.container = container

    # Роутеры
    app.include_router(api_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")

    # Обработчики ошибок
    @app.exception_handler(CaptchaLimitExceeded)
    async def captcha_limit_handler(request: Request, exc: CaptchaLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": str(exc), "error_code": "CAPTCHA_LIMIT_EXCEEDED"},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc), "error_code": type(exc).__name__},
        )

    return app
