"""Зависимости для FastAPI endpoints."""

from fastapi import Request

from src.application.fssp_service import FsspService
from src.application.task_manager import TaskManager
from src.infrastructure.config import Settings
from src.infrastructure.di import Container


def get_container(request: Request) -> Container:
    """
    Получить контейнер зависимостей из состояния приложения.

    Args:
        request: FastAPI запрос

    Returns:
        Контейнер зависимостей

    Raises:
        RuntimeError: Если контейнер не инициализирован
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("DI контейнер не инициализирован")
    return container


def get_settings(request: Request) -> Settings:
    """
    Получить настройки приложения.

    Args:
        request: FastAPI запрос

    Returns:
        Настройки приложения
    """
    return get_container(request).settings


def get_fssp_service(request: Request) -> FsspService:
    """
    Получить сервис для работы с ФССП.

    Args:
        request: FastAPI запрос

    Returns:
        Сервис ФССП
    """
    return get_container(request).fssp_service


def get_task_manager(request: Request) -> TaskManager:
    """
    Получить менеджер задач.

    Args:
        request: FastAPI запрос

    Returns:
        Менеджер задач
    """
    return get_container(request).task_manager
