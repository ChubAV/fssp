"""Доменные модели для системы асинхронных задач."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Статусы выполнения задачи."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    """Типы задач для запросов к ФССП."""

    IP = "ip"
    PERSON = "person"
    INN = "inn"


class Task(BaseModel):
    """Доменная модель задачи."""

    id: str = Field(description="Уникальный идентификатор задачи")
    task_type: TaskType = Field(description="Тип задачи")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Статус выполнения")
    params: dict[str, Any] = Field(description="Параметры запроса")
    result: list[dict[str, Any]] | None = Field(default=None, description="Результат выполнения")
    error: str | None = Field(default=None, description="Сообщение об ошибке")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    started_at: datetime | None = Field(default=None, description="Время начала выполнения")
    completed_at: datetime | None = Field(default=None, description="Время завершения")

    def mark_running(self) -> "Task":
        """Отметить задачу как выполняющуюся."""
        return self.model_copy(update={"status": TaskStatus.RUNNING, "started_at": datetime.now()})

    def mark_completed(self, result: list[dict[str, Any]]) -> "Task":
        """Отметить задачу как завершённую с результатом."""
        return self.model_copy(
            update={
                "status": TaskStatus.COMPLETED,
                "result": result,
                "completed_at": datetime.now(),
            }
        )

    def mark_failed(self, error: str) -> "Task":
        """Отметить задачу как завершённую с ошибкой."""
        return self.model_copy(
            update={
                "status": TaskStatus.FAILED,
                "error": error,
                "completed_at": datetime.now(),
            }
        )
