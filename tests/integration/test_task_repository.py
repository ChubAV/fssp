"""Integration-тесты для TaskRepository."""

import pytest
from pathlib import Path
import tempfile

from src.infrastructure.task_repository import TaskRepository
from src.domain.task import Task, TaskType, TaskStatus


@pytest.fixture
async def temp_db():
    """Временная база данных для тестов."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    repo = TaskRepository(db_path)
    await repo.initialize()
    yield repo
    await repo.close()
    db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_create_task(temp_db):
    """Тест создания задачи."""
    # Arrange
    task = Task(
        id="test-1",
        task_type=TaskType.IP,
        params={"ip": "123/45/67/89"},
    )

    # Act
    created = await temp_db.create(task)

    # Assert
    assert created.id == "test-1"
    assert created.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_get_task(temp_db):
    """Тест получения задачи."""
    # Arrange
    task = Task(id="test-2", task_type=TaskType.PERSON, params={"last_name": "Иванов"})
    await temp_db.create(task)

    # Act
    retrieved = await temp_db.get("test-2")

    # Assert
    assert retrieved is not None
    assert retrieved.id == "test-2"
    assert retrieved.task_type == TaskType.PERSON


@pytest.mark.asyncio
async def test_update_task(temp_db):
    """Тест обновления задачи."""
    # Arrange
    task = Task(id="test-3", task_type=TaskType.INN, params={"inn": "1234567890"})
    await temp_db.create(task)

    # Act
    updated_task = task.mark_running()
    await temp_db.update(updated_task)
    retrieved = await temp_db.get("test-3")

    # Assert
    assert retrieved.status == TaskStatus.RUNNING


@pytest.mark.asyncio
async def test_list_pending_tasks(temp_db):
    """Тест получения списка PENDING задач."""
    # Arrange
    task1 = Task(id="pending-1", task_type=TaskType.IP, params={})
    task2 = Task(id="pending-2", task_type=TaskType.PERSON, params={})
    task3 = Task(id="running-1", task_type=TaskType.INN, params={})
    
    await temp_db.create(task1)
    await temp_db.create(task2)
    await temp_db.create(task3.mark_running())

    # Act
    pending = await temp_db.list_pending()

    # Assert
    assert len(pending) == 2
    assert all(t.status == TaskStatus.PENDING for t in pending)
