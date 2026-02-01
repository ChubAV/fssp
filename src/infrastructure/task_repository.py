"""Репозиторий для хранения задач в SQLite."""
import json
import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from src.domain import Task, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class TaskRepository:
    """Асинхронный репозиторий задач с хранением в SQLite."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Инициализация БД и создание таблиц."""
        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                params TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)
        """)
        await self._connection.commit()
        logger.info("TaskRepository initialized", extra={"db_path": str(self._db_path)})

    async def close(self) -> None:
        """Закрытие соединения с БД."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("TaskRepository closed")

    def _task_to_row(self, task: Task) -> dict:
        """Преобразование Task в словарь для записи в БД."""
        return {
            "id": task.id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "params": json.dumps(task.params, ensure_ascii=False),
            "result": json.dumps(task.result, ensure_ascii=False) if task.result else None,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    def _row_to_task(self, row: aiosqlite.Row) -> Task:
        """Преобразование строки БД в Task."""
        return Task(
            id=row["id"],
            task_type=TaskType(row["task_type"]),
            status=TaskStatus(row["status"]),
            params=json.loads(row["params"]),
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

    async def create(self, task: Task) -> Task:
        """Создание новой задачи."""
        row = self._task_to_row(task)
        await self._connection.execute(
            """
            INSERT INTO tasks (id, task_type, status, params, result, error, created_at, started_at, completed_at)
            VALUES (:id, :task_type, :status, :params, :result, :error, :created_at, :started_at, :completed_at)
            """,
            row,
        )
        await self._connection.commit()
        logger.debug("Task created", extra={"task_id": task.id, "task_type": task.task_type.value})
        return task

    async def get(self, task_id: str) -> Task | None:
        """Получение задачи по ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    async def update(self, task: Task) -> Task:
        """Обновление существующей задачи."""
        row = self._task_to_row(task)
        await self._connection.execute(
            """
            UPDATE tasks SET
                status = :status,
                result = :result,
                error = :error,
                started_at = :started_at,
                completed_at = :completed_at
            WHERE id = :id
            """,
            row,
        )
        await self._connection.commit()
        logger.debug("Task updated", extra={"task_id": task.id, "status": task.status.value})
        return task

    async def delete(self, task_id: str) -> bool:
        """Удаление задачи по ID."""
        cursor = await self._connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )
        await self._connection.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug("Task deleted", extra={"task_id": task_id})
        return deleted

    async def list_all(
        self,
        status: TaskStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """Получение списка задач с опциональной фильтрацией по статусу."""
        if status:
            cursor = await self._connection.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status.value, limit, offset),
            )
        else:
            cursor = await self._connection.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]

    async def get_pending_tasks(self) -> list[Task]:
        """Получение всех задач в статусе PENDING."""
        cursor = await self._connection.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY created_at ASC",
            (TaskStatus.PENDING.value,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]

    async def count(self, status: TaskStatus | None = None) -> int:
        """Подсчёт количества задач."""
        if status:
            cursor = await self._connection.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE status = ?",
                (status.value,),
            )
        else:
            cursor = await self._connection.execute("SELECT COUNT(*) as cnt FROM tasks")
        row = await cursor.fetchone()
        return row["cnt"]
