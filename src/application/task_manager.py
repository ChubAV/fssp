"""Менеджер асинхронных задач с фоновой обработкой."""
import asyncio
import logging
import uuid
from typing import Any

from src.application.fssp_service import FsspService
from src.domain import Inn, IpNumber, Person, Task, TaskStatus, TaskType
from src.infrastructure.task_repository import TaskRepository

logger = logging.getLogger(__name__)


class TaskManager:
    """Менеджер для создания и фоновой обработки задач."""

    def __init__(self, repository: TaskRepository, fssp_service: FsspService):
        self._repository = repository
        self._fssp_service = fssp_service
        self._worker_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._task_added_event = asyncio.Event()

    async def start(self) -> None:
        """Запуск фонового воркера для обработки задач."""
        self._shutdown_event.clear()
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("TaskManager worker started")

    async def stop(self) -> None:
        """Остановка фонового воркера."""
        self._shutdown_event.set()
        self._task_added_event.set()  # Разбудить воркер для завершения
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=10.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            self._worker_task = None
        logger.info("TaskManager worker stopped")

    async def create_task(self, task_type: TaskType, params: dict[str, Any]) -> Task:
        """Создание новой задачи и добавление в очередь."""
        task = Task(
            id=str(uuid.uuid4()),
            task_type=task_type,
            params=params,
        )
        await self._repository.create(task)
        self._task_added_event.set()  # Сигнализировать воркеру о новой задаче
        logger.info("Task created", extra={"task_id": task.id, "task_type": task_type.value})
        return task

    async def get_task(self, task_id: str) -> Task | None:
        """Получение задачи по ID."""
        return await self._repository.get(task_id)

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """Получение списка задач."""
        return await self._repository.list_all(status=status, limit=limit, offset=offset)

    async def delete_task(self, task_id: str) -> bool:
        """Удаление задачи."""
        return await self._repository.delete(task_id)

    async def get_stats(self) -> dict[str, int]:
        """Получение статистики по задачам."""
        total = await self._repository.count()
        pending = await self._repository.count(TaskStatus.PENDING)
        running = await self._repository.count(TaskStatus.RUNNING)
        completed = await self._repository.count(TaskStatus.COMPLETED)
        failed = await self._repository.count(TaskStatus.FAILED)
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
        }

    async def _worker_loop(self) -> None:
        """Основной цикл воркера для обработки задач."""
        logger.debug("Worker loop started")
        while not self._shutdown_event.is_set():
            # Получаем задачи в статусе PENDING
            pending_tasks = await self._repository.get_pending_tasks()

            if not pending_tasks:
                # Ждём сигнала о новой задаче или таймаут
                self._task_added_event.clear()
                try:
                    await asyncio.wait_for(self._task_added_event.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass
                continue

            # Обрабатываем задачи по очереди
            for task in pending_tasks:
                if self._shutdown_event.is_set():
                    break
                await self._process_task(task)

        logger.debug("Worker loop finished")

    async def _process_task(self, task: Task) -> None:
        """Обработка одной задачи."""
        logger.info("Processing task", extra={"task_id": task.id, "task_type": task.task_type.value})

        # Отмечаем задачу как выполняющуюся
        task = task.mark_running()
        await self._repository.update(task)

        try:
            result = await self._execute_task(task)
            task = task.mark_completed(result)
            logger.info("Task completed", extra={"task_id": task.id, "result_count": len(result)})
        except Exception as e:
            error_msg = str(e)
            task = task.mark_failed(error_msg)
            logger.error("Task failed", extra={"task_id": task.id, "error": error_msg})

        await self._repository.update(task)

    async def _execute_task(self, task: Task) -> list[dict[str, Any]]:
        """Выполнение задачи в зависимости от её типа."""
        match task.task_type:
            case TaskType.IP:
                ip_number = IpNumber(ip=task.params["ip"])
                result = await self._fssp_service.by_ip(ip_number)
            case TaskType.PERSON:
                person = Person(**task.params)
                result = await self._fssp_service.by_person(person)
            case TaskType.INN:
                inn = Inn(inn=task.params["inn"])
                result = await self._fssp_service.by_inn(inn)
            case _:
                raise ValueError(f"Unknown task type: {task.task_type}")

        return [item.model_dump() for item in result.items]
