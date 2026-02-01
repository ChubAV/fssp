"""HTTP схемы для API задач."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain import TaskStatus, TaskType


class CreateTaskRequest(BaseModel):
    """Запрос на создание задачи."""

    params: dict[str, Any] = Field(description="Параметры запроса")


class TaskResponse(BaseModel):
    """Ответ с информацией о задаче."""

    id: str = Field(description="Уникальный идентификатор задачи")
    task_type: TaskType = Field(description="Тип задачи")
    status: TaskStatus = Field(description="Статус выполнения")
    params: dict[str, Any] = Field(description="Параметры запроса")
    result: list[dict[str, Any]] | None = Field(default=None, description="Результат выполнения")
    error: str | None = Field(default=None, description="Сообщение об ошибке")
    created_at: datetime = Field(description="Время создания")
    started_at: datetime | None = Field(default=None, description="Время начала выполнения")
    completed_at: datetime | None = Field(default=None, description="Время завершения")


class TaskListResponse(BaseModel):
    """Ответ со списком задач."""

    tasks: list[TaskResponse] = Field(description="Список задач")
    total: int = Field(description="Общее количество задач")


class TaskStatsResponse(BaseModel):
    """Статистика по задачам."""

    total: int = Field(description="Всего задач")
    pending: int = Field(description="Ожидают выполнения")
    running: int = Field(description="Выполняются")
    completed: int = Field(description="Завершены успешно")
    failed: int = Field(description="Завершены с ошибкой")


class TaskCreatedResponse(BaseModel):
    """Ответ при создании задачи."""

    id: str = Field(description="Идентификатор созданной задачи")
    status: TaskStatus = Field(description="Начальный статус задачи")
    message: str = Field(default="Задача создана и добавлена в очередь на обработку")
