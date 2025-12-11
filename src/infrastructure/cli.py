"""CLI клиент для запуска запросов к ФССП с красивым выводом."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated, Any

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from src.application.fssp_service import FsspService
from src.domain import DebtorCaseList, Inn, IpNumber, Person
from src.domain.errors import (
    CaptchaError,
    CaptchaLimitExceeded,
    DomainError,
    FsspUnavailable,
    ParsingError,
)
from src.infrastructure.captcha import CaptchaSolver
from src.infrastructure.config import create_settings
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.logging import setup_logging
from src.infrastructure.parser import FsspHtmlParser

app = typer.Typer(
    name="fssp",
    help="CLI клиент для поиска исполнительных производств на fssp.gov.ru",
    add_completion=False,
)
console = Console()


def render_human_table(result: DebtorCaseList) -> None:
    """Вывод результатов в виде красивой таблицы."""
    if not result.items:
        console.print("[yellow]Результаты не найдены[/yellow]")
        return

    table = Table(title="Исполнительные производства", show_header=True, header_style="bold magenta")
    table.add_column("№", style="cyan", width=4)
    table.add_column("Должник", style="green", width=30)
    table.add_column("Номер ИП", style="blue", width=20)
    table.add_column("Регион", style="yellow", width=20)
    table.add_column("Документ", style="white", width=25)
    table.add_column("Сумма долга", style="red", width=15)
    table.add_column("Отдел", style="white", width=25)
    table.add_column("Пристав", style="white", width=25)

    for idx, item in enumerate(result.items, start=1):
        table.add_row(
            str(idx),
            item.debtor,
            item.ip,
            item.region or "[dim]не указан[/dim]",
            item.doc,
            item.debt,
            item.office,
            item.bailiff,
        )

    console.print(table)

    # Дополнительная информация об основаниях окончания
    for idx, item in enumerate(result.items, start=1):
        if item.end_reason:
            console.print(
                f"[dim]№{idx}. Основание окончания:[/dim] [yellow]{item.end_reason}[/yellow]"
            )


def render_json(result: DebtorCaseList) -> None:
    """Вывод результатов в формате JSON."""
    payload: dict[str, Any] = result.model_dump()
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


async def execute_search(
    service: FsspService,
    search_type: str,
    **kwargs: Any,
) -> DebtorCaseList:
    """Выполняет поиск с индикацией прогресса."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Выполняется поиск по {search_type}...", total=None)

        if search_type == "ip":
            ip_number = IpNumber(ip=kwargs["ip_number"])
            result = await service.by_ip(ip_number)
        elif search_type == "person":
            person = Person(
                last_name=kwargs["last_name"],
                first_name=kwargs["first_name"],
                patronymic=kwargs.get("patronymic"),
                birthday=kwargs["birthday"],
            )
            result = await service.by_person(person)
        elif search_type == "inn":
            inn = Inn(inn=kwargs["inn"])
            result = await service.by_inn(inn)
        else:
            raise ValueError(f"Неизвестный тип поиска: {search_type}")

        progress.update(task, completed=True)

    return result


@app.command()
def ip(
    ip_number: Annotated[str, typer.Option("--ip-number", "-i", help="Номер ИП в формате 1234567/12/34/56")],
    format: Annotated[str, typer.Option("--format", "-f", help="Формат вывода (human/json)", case_sensitive=False)] = "human",
) -> None:
    """Поиск по номеру исполнительного производства."""
    asyncio.run(_run_search("ip", format=format, ip_number=ip_number))


@app.command()
def person(
    last_name: Annotated[str, typer.Option("--last-name", "-l", help="Фамилия")],
    first_name: Annotated[str, typer.Option("--first-name", help="Имя")],
    birthday: Annotated[str, typer.Option("--birthday", "-b", help="Дата рождения DD.MM.YYYY")],
    patronymic: Annotated[str | None, typer.Option("--patronymic", "-p", help="Отчество (опционально)")] = None,
    format: Annotated[str, typer.Option("--format", help="Формат вывода (human/json)", case_sensitive=False)] = "human",
) -> None:
    """Поиск по ФИО и дате рождения."""
    asyncio.run(_run_search("person", format=format, last_name=last_name, first_name=first_name, patronymic=patronymic, birthday=birthday))


@app.command()
def inn(
    inn: Annotated[str, typer.Option("--inn", "-i", help="ИНН (10 или 12 цифр)")],
    format: Annotated[str, typer.Option("--format", "-f", help="Формат вывода (human/json)", case_sensitive=False)] = "human",
) -> None:
    """Поиск по ИНН юридического лица."""
    asyncio.run(_run_search("inn", format=format, inn=inn))


async def _run_search(search_type: str, format: str, **kwargs: Any) -> None:
    """Внутренняя функция для выполнения поиска."""
    settings = create_settings()
    setup_logging(
        log_path=settings.LOG_PATH,
        max_bytes=settings.LOG_FILE_MAX_BYTES,
        backup_count=settings.LOG_FILE_BACKUP_COUNT,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )

    if settings.captcha is None or not settings.captcha.api_key:
        console.print(
            Panel(
                "[red]Ошибка:[/red] Не задан API ключ RuCaptcha (RUCAPTCH_API_KEY)",
                title="[bold red]Ошибка конфигурации[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    solver = CaptchaSolver(settings.captcha.api_key)
    client = FsspClient(solver)
    parser = FsspHtmlParser()
    service = FsspService(settings, client, parser)

    try:
        result = await execute_search(service, search_type, **kwargs)
    except (ValidationError, ValueError) as exc:
        console.print(f"[red]Ошибка:[/red] Некорректные входные данные: {exc}")
        raise typer.Exit(1)
    except CaptchaLimitExceeded as exc:
        console.print(
            Panel(
                f"[red]Превышено количество попыток ввода капчи:[/red] {exc}",
                title="[bold red]Ошибка капчи[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(2)
    except CaptchaError as exc:
        console.print(
            Panel(
                f"[red]Ошибка распознавания капчи:[/red] {exc}",
                title="[bold red]Ошибка капчи[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(3)
    except ParsingError as exc:
        console.print(
            Panel(
                f"[red]Ошибка парсинга ответа ФССП:[/red] {exc}",
                title="[bold red]Ошибка парсинга[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(4)
    except FsspUnavailable as exc:
        console.print(
            Panel(
                f"[red]ФССП недоступен или вернул пустой ответ:[/red] {exc}",
                title="[bold red]Сервис недоступен[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(5)
    except DomainError as exc:
        console.print(
            Panel(
                f"[red]Доменная ошибка:[/red] {exc}",
                title="[bold red]Ошибка[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(6)

    if format.lower() == "json":
        render_json(result)
    else:
        render_human_table(result)


def main() -> None:
    """Точка входа в CLI."""
    app()


if __name__ == "__main__":
    main()
