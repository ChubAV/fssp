import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.task_manager import TaskManager
from src.domain.errors import CaptchaLimitExceeded, DomainError
from src.infrastructure.captcha import CaptchaSolver
from src.infrastructure.config import Settings
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.parser import FsspHtmlParser
from src.infrastructure.task_repository import TaskRepository
from src.application.fssp_service import FsspService

from .api import router as api_router
from .middleware import add_request_context
from .tasks_api import router as tasks_router

logger = logging.getLogger(__name__)


def _build_fssp_service(settings: Settings) -> FsspService:
    """Создание экземпляра FsspService."""
    captcha_solver = CaptchaSolver(
        api_key=settings.captcha.api_key if settings.captcha else settings.RUCAPTCH_API_KEY
    )
    client = FsspClient(captcha_solver=captcha_solver)
    parser = FsspHtmlParser()
    return FsspService(settings=settings, client=client, parser=parser)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    settings: Settings = app.settings

    # Инициализация репозитория задач
    db_path = settings.DATABASE_PATH
    repository = TaskRepository(db_path)
    await repository.initialize()
    logger.info("Task repository initialized", extra={"db_path": str(db_path)})

    # Создание FsspService
    fssp_service = _build_fssp_service(settings)
    app.state.fssp_service = fssp_service

    # Создание и запуск TaskManager
    task_manager = TaskManager(repository=repository, fssp_service=fssp_service)
    await task_manager.start()
    app.state.task_manager = task_manager
    logger.info("Task manager started")

    yield

    # Остановка TaskManager
    await task_manager.stop()
    logger.info("Task manager stopped")

    # Закрытие репозитория
    await repository.close()
    logger.info("Task repository closed")


def create_app(settings: Settings):
    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
    app.middleware("http")(add_request_context)
    app.settings = settings

    # Роутеры
    app.include_router(api_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")

    @app.exception_handler(CaptchaLimitExceeded)
    async def captcha_limit_handler(request: Request, exc: CaptchaLimitExceeded):  # noqa: WPS430
        return JSONResponse(
            status_code=429,
            content={"detail": str(exc), "error_code": "CAPTCHA_LIMIT_EXCEEDED"},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):  # noqa: WPS430
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app
