"""API эндпоинты для управления асинхронными задачами."""
from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.task_manager import TaskManager
from src.domain import TaskStatus, TaskType

from .dependencies import get_task_manager
from .schemas import (
    CreateTaskRequest,
    TaskCreatedResponse,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/{task_type}",
    description="Создать асинхронную задачу для получения данных из ФССП",
    response_model=TaskCreatedResponse,
    status_code=202,
)
async def create_task(
    task_type: TaskType,
    request: CreateTaskRequest,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Создаёт задачу для асинхронной обработки.

    Параметры:
    - **task_type**: Тип задачи (ip, person, inn)
    - **params**: Параметры запроса в зависимости от типа:
        - ip: {"ip": "номер ИП"}
        - person: {"last_name": "...", "first_name": "...", "birthday": "DD.MM.YYYY", "patronymic": "..."}
        - inn: {"inn": "ИНН"}

    Возвращает ID созданной задачи для последующего получения результата.
    """
    task = await task_manager.create_task(task_type, request.params)
    return TaskCreatedResponse(id=task.id, status=task.status)


@router.get(
    "",
    description="Получить список задач с опциональной фильтрацией",
    response_model=TaskListResponse,
)
async def list_tasks(
    status: TaskStatus | None = Query(default=None, description="Фильтр по статусу"),
    limit: int = Query(default=100, ge=1, le=1000, description="Максимальное количество задач"),
    offset: int = Query(default=0, ge=0, description="Смещение для пагинации"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Получить список всех задач с возможностью фильтрации по статусу."""
    tasks = await task_manager.list_tasks(status=status, limit=limit, offset=offset)
    stats = await task_manager.get_stats()
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t.model_dump()) for t in tasks],
        total=stats["total"],
    )


@router.get(
    "/stats",
    description="Получить статистику по задачам",
    response_model=TaskStatsResponse,
)
async def get_stats(
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Получить статистику по задачам: количество в каждом статусе."""
    stats = await task_manager.get_stats()
    return TaskStatsResponse(**stats)


@router.get(
    "/{task_id}",
    description="Получить информацию о задаче по ID",
    response_model=TaskResponse,
)
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Получить информацию о задаче, включая статус и результат выполнения.

    Статусы:
    - **pending**: Задача ожидает обработки
    - **running**: Задача выполняется
    - **completed**: Задача выполнена успешно, результат в поле `result`
    - **failed**: Задача завершилась с ошибкой, сообщение в поле `error`
    """
    task = await task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
    return TaskResponse.model_validate(task.model_dump())


@router.delete(
    "/{task_id}",
    description="Удалить задачу",
    status_code=204,
)
async def delete_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Удалить задачу по ID."""
    deleted = await task_manager.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
