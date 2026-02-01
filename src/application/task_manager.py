"""Менеджер асинхронных задач с фоновой обработкой."""
import asyncio
import uuid
from typing import Any

import structlog

from src.application.fssp_service import FsspService
from src.application.retry_policy import retry_with_backoff
from src.domain import Inn, IpNumber, Person, Task, TaskStatus, TaskType
from src.domain.errors import DomainError, RetryableError
from src.domain.protocols import ITaskRepository

logger = structlog.get_logger()


class TaskManager:
    """Менеджер для создания и фоновой обработки задач."""

    def __init__(
        self,
        repository: ITaskRepository,
        fssp_service: FsspService,
        max_concurrent_tasks: int = 5,
        retry_max_attempts: int = 3,
    ):
        """
        Инициализация менеджера задач.

        Args:
            repository: Репозиторий для хранения задач
            fssp_service: Сервис для работы с ФССП
            max_concurrent_tasks: Максимальное количество одновременно обрабатываемых задач
            retry_max_attempts: Максимальное количество попыток при ошибках
        """
        self._repository = repository
        self._fssp_service = fssp_service
        self._max_concurrent = max_concurrent_tasks
        self._retry_max_attempts = retry_max_attempts
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._worker_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._task_added_event = asyncio.Event()

    async def start(self) -> None:
        """Запуск фонового воркера для обработки задач."""
        self._shutdown_event.clear()
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("TaskManager worker запущен", max_concurrent=self._max_concurrent)

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Остановка фонового воркера.

        Args:
            timeout: Таймаут ожидания завершения воркера в секундах
        """
        self._shutdown_event.set()
        self._task_added_event.set()  # Разбудить воркер для завершения
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Таймаут остановки воркера, принудительная отмена")
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            self._worker_task = None
        logger.info("TaskManager worker остановлен")

    async def create_task(self, task_type: TaskType, params: dict[str, Any]) -> Task:
        """
        Создание новой задачи и добавление в очередь.

        Args:
            task_type: Тип задачи
            params: Параметры задачи

        Returns:
            Созданная задача
        """
        task = Task(
            id=str(uuid.uuid4()),
            task_type=task_type,
            params=params,
        )
        await self._repository.create(task)
        self._task_added_event.set()  # Сигнализировать воркеру о новой задаче
        logger.info("Задача создана", task_id=task.id, task_type=task_type.value)
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
        logger.debug("Worker loop запущен")
        while not self._shutdown_event.is_set():
            try:
                # Получаем задачи в статусе PENDING
                pending_tasks = await self._repository.list_pending(limit=self._max_concurrent * 2)

                if not pending_tasks:
                    # Ждём сигнала о новой задаче или таймаут
                    self._task_added_event.clear()
                    try:
                        await asyncio.wait_for(self._task_added_event.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        pass
                    continue

                # Обрабатываем задачи параллельно с ограничением
                logger.debug("Обработка задач", count=len(pending_tasks))
                await asyncio.gather(
                    *[self._process_task_safe(task) for task in pending_tasks],
                    return_exceptions=True,
                )
            except asyncio.CancelledError:
                logger.info("Worker loop отменён")
                raise
            except Exception as e:
                logger.error("Ошибка в worker loop", error=str(e), error_type=type(e).__name__)
                await asyncio.sleep(1.0)

        logger.debug("Worker loop завершён")

    async def _process_task_safe(self, task: Task) -> None:
        """
        Безопасная обработка задачи с семафором.

        Args:
            task: Задача для обработки
        """
        async with self._semaphore:
            try:
                await self._process_task(task)
            except Exception as e:
                logger.error(
                    "Критическая ошибка при обработке задачи",
                    task_id=task.id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

    async def _process_task(self, task: Task) -> None:
        """
        Обработка одной задачи.

        Args:
            task: Задача для обработки
        """
        logger.info("Обработка задачи", task_id=task.id, task_type=task.task_type.value)

        # Отмечаем задачу как выполняющуюся
        task = task.mark_running()
        await self._repository.update(task)

        try:
            # Выполняем задачу с retry-логикой для retryable ошибок
            async def execute_with_retry():
                return await self._execute_task(task)

            result = await retry_with_backoff(
                execute_with_retry,
                max_attempts=self._retry_max_attempts,
                retryable_exceptions=(RetryableError,),
            )
            task = task.mark_completed(result)
            logger.info("Задача выполнена успешно", task_id=task.id, result_count=len(result))
        except DomainError as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            task = task.mark_failed(error_msg)
            logger.error("Задача завершена с доменной ошибкой", task_id=task.id, error=error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {type(e).__name__}: {str(e)}"
            task = task.mark_failed(error_msg)
            logger.error(
                "Задача завершена с неожиданной ошибкой",
                task_id=task.id,
                error=error_msg,
                error_type=type(e).__name__,
            )

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
