# FSSP — сервис поиска исполнительных производств

Микросервис для автоматизированного поиска сведений об исполнительных производствах на сайте [fssp.gov.ru](https://fssp.gov.ru/) с REST API, CLI и MCP‑сервером для интеграции с AI‑клиентами (Cursor, Claude Desktop и др.).

## Возможности

- Поиск по номеру ИП, ФИО + дате рождения или ИНН
- Автоматическое решение капчи через RuCaptcha
- REST API на FastAPI и CLI на Typer/Rich
- MCP Server (Model Context Protocol) с инструментами поиска по номеру ИП, ФИО+ДР и ИНН
- Асинхронная обработка задач с retry-логикой и параллелизмом
- Вывод результатов в человеко‑читаемом виде и в JSON
- Структурированное логирование и ротация логов

## Архитектура

Проект следует принципам **Clean Architecture** с чистым разделением слоев:

- **Domain Layer**: доменные модели, бизнес-правила, протоколы (интерфейсы)
- **Application Layer**: бизнес-логика, оркестрация, use cases
- **Infrastructure Layer**: внешние зависимости (HTTP, БД, Playwright, MCP)

**Основные паттерны:**
- Dependency Injection через контейнер (`src/infrastructure/di.py`)
- Инверсия зависимостей (Domain не зависит от Infrastructure)
- Protocol-based design для тестируемости
- DTO для разделения API и Domain моделей
- Retry pattern с экспоненциальным backoff

## Технологии

- Python 3.13+, FastAPI, Pydantic, Typer, Rich, Structlog
- Playwright для работы с сайтом ФССП
- uv как менеджер пакетов/раннер
- FastMCP (MCP server) для интеграции с AI‑клиентами
- Docker (готовый образ для продакшена)
- pytest, pytest-asyncio, pytest-cov для тестирования
- ruff для линтинга и форматирования

## Требования

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- [just](https://github.com/casey/just) (опционально)

## Быстрый старт (локально)

```bash
git clone <repository-url>
cd fssp
uv sync
uv run playwright install chromium
cp .env.example .env  # при наличии, либо заполните вручную
```

Минимальный `.env`:
```bash
RUCAPTCH_API_KEY=your_rucaptcha_api_key_here
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### Запуск HTTP API

- Дев-сервер с автоперезапуском: `just dev`
- Продакшен без автоперезапуска: `just run`
- Кастомный хост/порт: `just dev HOST=127.0.0.1 PORT=8080`

API доступно на `http://localhost:8000`, документация:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### CLI

- По номеру ИП: `just cli ip --ip-number "1234567/12/34/56"`
- По ФИО: `just cli person --last-name "Иванов" --first-name "Иван" --birthday "16.05.1992"`
- По ИНН: `just cli inn --inn "1234567890"`
- Вывод в JSON: добавить `--format json`

### MCP Server

- Стандартный режим (stdio) для локальной интеграции с AI‑клиентом: `just mcp`
- HTTP‑режим (по умолчанию `0.0.0.0:8100`): `just mcp-http` (можно переопределить `MCP_HOST` и `MCP_PORT`)

MCP‑сервер предоставляет три инструмента:
- `search_by_ip(ip_number: str)` — поиск по номеру ИП/СД/СВ
- `search_by_person(last_name, first_name, birthday, patronymic?)` — поиск по ФИО и дате рождения
- `search_by_inn(inn: str)` — поиск по ИНН (физ/юр лицо)

## Запуск в Docker

Dockerfile собирает продакшен-образ с установленным Chromium и зависимостями Playwright.

1) Собрать образ:
```bash
docker build -t fssp .
```

2) Запустить контейнер (пример с `.env` и монтированием логов/временных файлов):
```bash
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/temp:/app/temp" \
  fssp
```

- Переменные `HOST`, `PORT`, `DEBUG` заданы в образе по умолчанию, `RUCAPTCH_API_KEY` обязателен.
- Playwright и его зависимости устанавливаются на этапе сборки, дополнительных шагов не требуется.

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `RUCAPTCH_API_KEY` | API-ключ RuCaptcha (обязательно) | — |
| `DEBUG` | Режим отладки | `false` |
| `HOST` | Хост HTTP сервера | `0.0.0.0` |
| `PORT` | Порт HTTP сервера | `8000` |
| `MCP_TRANSPORT` | Транспорт MCP (`stdio` или `http`) | `stdio` |
| `MCP_HOST` | Хост MCP‑HTTP сервера | `0.0.0.0` |
| `MCP_PORT` | Порт MCP‑HTTP сервера | `8100` |

## Форматы входных данных

- Номер ИП: `1234567/12/34/56` или `1234567/12/34/56-ИП`
- Дата рождения: `DD.MM.YYYY` (например, `16.05.1992`)
- ИНН: 10 цифр (юрлицо) или 12 цифр (физлицо)

## Ошибки и логирование

- Коды доменных ошибок: `CaptchaError`, `CaptchaLimitExceeded`, `FsspUnavailable`, `ParsingError`, `ValidationError`.
- Логи в `logs/main.log` с ротацией (5 МБ, 3 бэкапа). Уровень зависит от `DEBUG`.

## Разработка

### Установка зависимостей

```bash
# Основные зависимости
uv sync

# С dev-зависимостями (для разработки и тестирования)
uv sync --extra dev
```

### Запуск тестов

```bash
# Все тесты
just test

# Тесты с покрытием
just test-cov

# Только unit-тесты
just test-unit

# Только integration-тесты
just test-integration

# Только e2e-тесты
just test-e2e
```

### Линтинг и форматирование

```bash
# Проверка стиля кода
just lint

# Автоматическое форматирование
just fmt

# Полная проверка (lint + tests)
just check
```

### Текущее покрытие тестами

- **Domain модели**: 97%
- **Infrastructure (parser, config, DI)**: 88-98%
- **Application (services)**: требует расширения
- **Общее покрытие**: ~58% (цель: >80%)

## Структура проекта

```
fssp/
├── src/
│   ├── domain/                      # Доменный слой
│   │   ├── models.py               # Доменные модели и value objects
│   │   ├── task.py                 # Модель задачи
│   │   ├── errors.py               # Доменные ошибки
│   │   └── protocols.py            # Протоколы (интерфейсы)
│   ├── application/                 # Слой бизнес-логики
│   │   ├── fssp_service.py         # Сервис работы с ФССП
│   │   ├── task_manager.py         # Менеджер асинхронных задач
│   │   └── retry_policy.py         # Политика повторных попыток
│   └── infrastructure/              # Инфраструктурный слой
│       ├── config.py               # Конфигурация
│       ├── di.py                   # DI контейнер
│       ├── fssp_client.py          # HTTP-клиент (Playwright)
│       ├── parser.py               # Парсер HTML
│       ├── url_builder.py          # Построитель URL
│       ├── captcha.py              # Решение капчи
│       ├── task_repository.py      # Репозиторий задач (SQLite)
│       ├── http/                   # HTTP API
│       │   ├── app.py              # FastAPI приложение
│       │   ├── api.py              # REST endpoints
│       │   ├── dependencies.py     # FastAPI dependencies
│       │   └── schemas/            # DTO (Data Transfer Objects)
│       │       ├── search.py       # DTO для поиска
│       │       └── task.py         # DTO для задач
│       ├── cli.py                  # CLI интерфейс
│       └── mcp/                    # MCP сервер
│           └── server.py
├── tests/                           # Тесты
│   ├── unit/                       # Unit-тесты
│   │   ├── domain/                 # Тесты доменных моделей
│   │   ├── application/            # Тесты сервисов
│   │   └── infrastructure/         # Тесты инфраструктуры
│   ├── integration/                # Интеграционные тесты
│   └── e2e/                        # End-to-end тесты
├── logs/                           # Логи приложения
├── temp/                           # Временные файлы (капчи, скриншоты)
├── main.py                         # Точка входа (FastAPI factory)
├── mcp_server.py                   # Точка входа MCP server
├── pyproject.toml                  # Зависимости и конфигурация
├── justfile                        # Скрипты для разработки
└── README.md
```



## Автор

chub.aleksandr.v@gmail.com
