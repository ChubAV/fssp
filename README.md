# FSSP Service

Микросервис для автоматизированного поиска исполнительных производств на сайте [ФССП России](https://fssp.gov.ru/).

Предоставляет REST API, CLI и MCP-сервер для интеграции с AI-клиентами (Cursor, Claude Desktop и др.).

## Возможности

- **Три типа поиска**: по номеру ИП, по ФИО + дате рождения, по ИНН
- **Автоматическое решение капчи** через RuCaptcha
- **REST API** (FastAPI) с автодокументацией Swagger/ReDoc
- **CLI** (Typer + Rich) для работы из терминала
- **MCP Server** для интеграции с AI-ассистентами
- **Детальный парсинг** данных о должнике, документах и задолженности
- **Структурированное логирование** с ротацией файлов

## Быстрый старт

### Требования

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) — менеджер пакетов
- [just](https://github.com/casey/just) — task runner (опционально)

### Установка

```bash
git clone <repository-url>
cd fssp
uv sync
uv run playwright install chromium
```

### Конфигурация

Создайте файл `.env`:

```bash
RUCAPTCH_API_KEY=your_rucaptcha_api_key  # обязательно
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### Запуск

```bash
# HTTP API (dev-режим с автоперезапуском)
just dev

# HTTP API (production)
just run

# CLI
just cli ip --ip-number "1234567/12/34/56"
just cli person --last-name "Иванов" --first-name "Иван" --birthday "16.05.1992"
just cli inn --inn "1234567890"

# MCP Server
just mcp          # stdio (для локальной интеграции)
just mcp-http     # HTTP (порт 8100)
```

## REST API

После запуска документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/healthcheck` | Проверка работоспособности |
| POST | `/ip` | Поиск по номеру ИП |
| POST | `/person` | Поиск по ФИО и дате рождения |
| POST | `/inn` | Поиск по ИНН |

### Примеры запросов

**Поиск по номеру ИП:**
```bash
curl -X POST http://localhost:8000/ip \
  -H "Content-Type: application/json" \
  -d '{"ip_number": "1234567/12/34/56"}'
```

**Поиск по ФИО:**
```bash
curl -X POST http://localhost:8000/person \
  -H "Content-Type: application/json" \
  -d '{
    "last_name": "Иванов",
    "first_name": "Иван",
    "patronymic": "Иванович",
    "birthday": "16.05.1992"
  }'
```

**Поиск по ИНН:**
```bash
curl -X POST http://localhost:8000/inn \
  -H "Content-Type: application/json" \
  -d '{"inn": "1234567890"}'
```

### Формат ответа

```json
{
  "items": [
    {
      "region": "Московская область",
      "debtor": "Иванов Иван Иванович 01.01.1990",
      "debtor_type": "physical",
      "debtor_last_name": "Иванов",
      "debtor_first_name": "Иван",
      "debtor_patronymic": "Иванович",
      "debtor_birthday": "01.01.1990",
      "debtor_birthplace": "г. Москва",
      "ip": "12345/21/50001-ИП",
      "doc": "2-1234/2021 от 01.01.2021",
      "doc_basis": "Судебный приказ",
      "doc_issuer": "Мировой судья судебного участка №1",
      "creditor_inn": "7707083893",
      "end_reason": null,
      "debt": "Задолженность: 50000.00 руб.",
      "debt_type": "Иные взыскания имущественного характера",
      "debt_amount": "50000.00",
      "debt_remaining": "25000.00",
      "debt_bailiff_fee": "3500.00",
      "office": "Одинцовское РОСП",
      "bailiff": "Петров П.П."
    }
  ],
  "total": 1
}
```

## CLI

```bash
# Поиск по номеру ИП
just cli ip --ip-number "1234567/12/34/56"

# Поиск по ФИО (отчество опционально)
just cli person --last-name "Иванов" --first-name "Иван" --birthday "16.05.1992"
just cli person --last-name "Иванов" --first-name "Иван" --patronymic "Иванович" --birthday "16.05.1992"

# Поиск по ИНН
just cli inn --inn "1234567890"      # юрлицо (10 цифр)
just cli inn --inn "123456789012"    # физлицо (12 цифр)

# Вывод в JSON
just cli ip --ip-number "1234567/12/34/56" --format json
```

## MCP Server

MCP (Model Context Protocol) сервер для интеграции с AI-клиентами.

### Инструменты

| Инструмент | Параметры | Описание |
|------------|-----------|----------|
| `search_by_ip` | `ip_number` | Поиск по номеру ИП/СД/СВ |
| `search_by_person` | `last_name`, `first_name`, `birthday`, `patronymic?` | Поиск по ФИО |
| `search_by_inn` | `inn` | Поиск по ИНН |

### Запуск

```bash
# stdio (стандартный режим для Cursor, Claude Desktop)
just mcp

# HTTP-режим
just mcp-http
MCP_HOST=127.0.0.1 MCP_PORT=8200 just mcp-http
```

### Настройка в Cursor

Добавьте в `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "fssp": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "/path/to/fssp"
    }
  }
}
```

## Docker

```bash
# Сборка
docker build -t fssp .

# Запуск
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/temp:/app/temp" \
  fssp
```

Playwright и Chromium устанавливаются автоматически при сборке образа.

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `RUCAPTCH_API_KEY` | API-ключ RuCaptcha | — (обязательно) |
| `DEBUG` | Режим отладки | `false` |
| `HOST` | Хост HTTP-сервера | `0.0.0.0` |
| `PORT` | Порт HTTP-сервера | `8000` |
| `MCP_TRANSPORT` | Транспорт MCP: `stdio` или `http` | `stdio` |
| `MCP_HOST` | Хост MCP HTTP-сервера | `0.0.0.0` |
| `MCP_PORT` | Порт MCP HTTP-сервера | `8100` |

## Форматы входных данных

| Тип | Формат | Примеры |
|-----|--------|---------|
| Номер ИП | `NNNNNNN/NN/NN/NN` или `NNNNNNN/NN/NNNNN-ИП/СД/СВ` | `1234567/12/34/56`, `1234567/12/34567-ИП` |
| Дата рождения | `DD.MM.YYYY` | `16.05.1992` |
| ИНН юрлица | 10 цифр | `1234567890` |
| ИНН физлица | 12 цифр | `123456789012` |

## Архитектура

Проект следует принципам **Clean Architecture**:

```
src/
├── domain/           # Доменный слой
│   ├── models.py     # Модели данных (Person, Inn, IpNumber, DebtorCase)
│   ├── errors.py     # Доменные ошибки
│   ├── task.py       # Модель асинхронной задачи
│   └── protocols.py  # Интерфейсы (протоколы)
├── application/      # Слой бизнес-логики
│   ├── fssp_service.py    # Основной сервис
│   ├── task_manager.py    # Менеджер задач
│   └── retry_policy.py    # Политика повторов
└── infrastructure/   # Инфраструктурный слой
    ├── config.py          # Конфигурация
    ├── di.py              # Dependency Injection
    ├── fssp_client.py     # Playwright-клиент
    ├── parser.py          # HTML-парсер
    ├── captcha.py         # Интеграция с RuCaptcha
    ├── http/              # REST API (FastAPI)
    ├── cli.py             # CLI (Typer)
    └── mcp/               # MCP Server
```

**Ключевые паттерны:**
- Dependency Injection через контейнер
- Protocol-based design для тестируемости
- DTO для разделения API и доменных моделей
- Retry с экспоненциальным backoff

## Разработка

### Установка dev-зависимостей

```bash
uv sync --extra dev
```

### Тесты

```bash
just test           # все тесты
just test-cov       # с покрытием
just test-unit      # unit-тесты
just test-integration  # интеграционные
just test-e2e       # end-to-end
```

### Линтинг

```bash
just lint           # проверка (ruff)
just fmt            # форматирование
just check          # lint + tests
```

## Обработка ошибок

Сервис возвращает структурированные ошибки:

| Код | Тип | Описание |
|-----|-----|----------|
| 400 | `ValidationError` | Некорректные входные данные |
| 502 | `FsspUnavailable` | Сайт ФССП недоступен |
| 502 | `CaptchaError` | Ошибка решения капчи |
| 429 | `CaptchaLimitExceeded` | Превышен лимит капчи |
| 500 | `ParsingError` | Ошибка парсинга HTML |

Логи записываются в `logs/main.log` с ротацией (5 МБ, 3 бэкапа).

## Технологии

- **Python 3.13+**, **FastAPI**, **Pydantic** — API и валидация
- **Playwright** — автоматизация браузера
- **FastMCP** — MCP-сервер
- **Typer**, **Rich** — CLI
- **Structlog** — логирование
- **pytest** — тестирование
- **ruff** — линтинг
- **uv** — менеджер пакетов
- **Docker** — контейнеризация

## Лицензия

MIT

## Автор

chub.aleksandr.v@gmail.com
