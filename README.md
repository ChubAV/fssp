# FSSP — сервис поиска исполнительных производств

Микросервис для автоматизированного поиска сведений об исполнительных производствах на сайте [fssp.gov.ru](https://fssp.gov.ru/) с REST API и CLI.

## Возможности

- Поиск по номеру ИП, ФИО + дате рождения или ИНН
- Автоматическое решение капчи через RuCaptcha
- REST API на FastAPI и CLI на Typer/Rich
- Вывод результатов в человеко‑читаемом виде и в JSON
- Структурированное логирование и ротация логов

## Технологии

- Python 3.13+, FastAPI, Pydantic, Typer, Rich, Structlog
- Playwright для работы с сайтом ФССП
- uv как менеджер пакетов/раннер
- Docker (готовый образ для продакшена)

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

## Форматы входных данных

- Номер ИП: `1234567/12/34/56` или `1234567/12/34/56-ИП`
- Дата рождения: `DD.MM.YYYY` (например, `16.05.1992`)
- ИНН: 10 цифр (юрлицо) или 12 цифр (физлицо)

## Ошибки и логирование

- Коды доменных ошибок: `CaptchaError`, `CaptchaLimitExceeded`, `FsspUnavailable`, `ParsingError`, `ValidationError`.
- Логи в `logs/main.log` с ротацией (5 МБ, 3 бэкапа). Уровень зависит от `DEBUG`.

## Структура проекта

```
fssp/
├── src/
│   ├── application/          # Бизнес-логика
│   ├── domain/               # Доменные модели и ошибки
│   └── infrastructure/       # Внешние зависимости (HTTP, CLI, Playwright)
├── logs/                     # Логи приложения
├── temp/                     # Временные файлы (капчи, скриншоты)
├── main.py                   # Точка входа (FastAPI factory)
├── pyproject.toml            # Зависимости проекта
├── justfile                  # Скрипты для разработки/запуска
└── README.md
```

## Лицензия

[Укажите лицензию проекта]

## Автор

[Укажите автора проекта]
