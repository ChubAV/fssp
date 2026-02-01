"""Контейнер зависимостей (Dependency Injection)."""

from dataclasses import dataclass

from src.application.fssp_service import FsspService
from src.application.task_manager import TaskManager
from src.domain.protocols import ITaskRepository
from src.infrastructure.captcha import CaptchaSolver
from src.infrastructure.config import Settings, create_settings
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.parser import FsspHtmlParser
from src.infrastructure.task_repository import TaskRepository
from src.infrastructure.url_builder import FsspUrlBuilder


@dataclass
class Container:
    """Контейнер со всеми зависимостями приложения."""

    settings: Settings
    fssp_service: FsspService
    task_manager: TaskManager
    task_repository: ITaskRepository


def build_container(settings: Settings | None = None) -> Container:
    """
    Построить контейнер зависимостей.

    Args:
        settings: Настройки приложения (если None, будут загружены из .env)

    Returns:
        Контейнер со всеми зависимостями
    """
    if settings is None:
        settings = create_settings()

    # Infrastructure layer
    captcha_solver = CaptchaSolver(settings.RUCAPTCH_API_KEY)
    fssp_client = FsspClient(
        captcha_solver=captcha_solver,
        browser_config=settings.browser,
        temp_path=settings.temp_path,
    )
    parser = FsspHtmlParser()
    url_builder = FsspUrlBuilder(settings.urls)
    task_repo: ITaskRepository = TaskRepository(settings.database_path)

    # Application layer
    fssp_service = FsspService(
        client=fssp_client,
        parser=parser,
        url_builder=url_builder,
    )
    task_manager = TaskManager(
        repository=task_repo,
        fssp_service=fssp_service,
        max_concurrent_tasks=5,
        retry_max_attempts=3,
    )

    return Container(
        settings=settings,
        fssp_service=fssp_service,
        task_manager=task_manager,
        task_repository=task_repo,
    )
