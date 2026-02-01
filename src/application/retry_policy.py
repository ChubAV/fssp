"""Политики повторных попыток для обработки временных сбоев."""

import asyncio
from typing import TypeVar, Callable, Awaitable

import structlog

from src.domain.errors import RetryableError

logger = structlog.get_logger()

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (RetryableError,),
) -> T:
    """
    Выполнить асинхронную функцию с повторными попытками и экспоненциальной задержкой.

    Args:
        func: Асинхронная функция для выполнения
        max_attempts: Максимальное количество попыток
        initial_delay: Начальная задержка в секундах
        backoff_factor: Множитель для увеличения задержки
        retryable_exceptions: Кортеж исключений, которые можно повторить

    Returns:
        Результат выполнения функции

    Raises:
        Exception: Последнее исключение, если все попытки исчерпаны
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug("Попытка выполнения операции", attempt=attempt, max_attempts=max_attempts)
            result = await func()
            if attempt > 1:
                logger.info("Операция успешно выполнена после повторных попыток", attempt=attempt)
            return result
        except retryable_exceptions as e:
            last_exception = e
            if attempt == max_attempts:
                logger.error(
                    "Все попытки исчерпаны",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(e),
                )
                raise

            delay = initial_delay * (backoff_factor ** (attempt - 1))
            logger.warning(
                "Ошибка при выполнении операции, повтор через задержку",
                attempt=attempt,
                max_attempts=max_attempts,
                delay=delay,
                error=str(e),
            )
            await asyncio.sleep(delay)

    # Этот код не должен быть достигнут, но для безопасности типов
    if last_exception:
        raise last_exception
    raise RuntimeError("Неожиданное состояние в retry_with_backoff")
