"""Протоколы (интерфейсы) для обеспечения инверсии зависимостей в Clean Architecture."""

from pathlib import Path
from typing import Protocol

from src.domain.models import Person
from src.domain.task import Task


class IFsspClient(Protocol):
    """Протокол для HTTP-клиента ФССП."""

    async def fetch(self, url: str) -> str:
        """
        Получить HTML результатов поиска с сайта ФССП.

        Args:
            url: URL для запроса

        Returns:
            HTML-строка с результатами

        Raises:
            FsspUnavailable: Сайт ФССП недоступен или вернул ошибку
            CaptchaError: Ошибка при решении капчи
        """
        ...


class IFsspParser(Protocol):
    """Протокол для парсера HTML результатов ФССП."""

    def parse_cases(self, html: str) -> list[dict]:
        """
        Распарсить HTML и извлечь информацию о делах.

        Args:
            html: HTML-строка для парсинга

        Returns:
            Список словарей с данными о делах

        Raises:
            ParsingError: Ошибка при парсинге HTML
            CaptchaLimitExceeded: Превышен лимит попыток ввода капчи
        """
        ...


class ICaptchaSolver(Protocol):
    """Протокол для сервиса решения капчи."""

    async def solve(self, image_path: Path) -> str:
        """
        Распознать текст капчи с изображения.

        Args:
            image_path: Путь к файлу с изображением капчи

        Returns:
            Распознанный текст капчи

        Raises:
            CaptchaError: Ошибка при распознавании капчи
        """
        ...


class ITaskRepository(Protocol):
    """Протокол для репозитория задач."""

    async def create(self, task: Task) -> Task:
        """
        Создать новую задачу.

        Args:
            task: Объект задачи для создания

        Returns:
            Созданная задача с ID
        """
        ...

    async def get(self, task_id: str) -> Task | None:
        """
        Получить задачу по ID.

        Args:
            task_id: Идентификатор задачи

        Returns:
            Объект задачи или None, если не найдена
        """
        ...

    async def update(self, task: Task) -> Task:
        """
        Обновить существующую задачу.

        Args:
            task: Объект задачи с обновленными данными

        Returns:
            Обновленная задача
        """
        ...

    async def list_pending(self, limit: int = 100) -> list[Task]:
        """
        Получить список задач в статусе PENDING.

        Args:
            limit: Максимальное количество задач для возврата

        Returns:
            Список задач в статусе PENDING
        """
        ...


class IUrlBuilder(Protocol):
    """Протокол для построителя URL запросов к ФССП."""

    def build_ip_url(self, ip_number: str) -> str:
        """
        Построить URL для поиска по номеру ИП.

        Args:
            ip_number: Номер исполнительного производства

        Returns:
            URL для запроса
        """
        ...

    def build_person_url(self, person: Person) -> str:
        """
        Построить URL для поиска по данным физического лица.

        Args:
            person: Данные о человеке (ФИО, дата рождения)

        Returns:
            URL для запроса
        """
        ...

    def build_inn_url(self, inn: str) -> str:
        """
        Построить URL для поиска по ИНН.

        Args:
            inn: ИНН физического или юридического лица

        Returns:
            URL для запроса
        """
        ...
