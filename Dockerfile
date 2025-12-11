# Используем официальный образ Python 3.13
FROM python:3.13-slim

# Устанавливаем системные зависимости для Playwright и других инструментов
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv
RUN uv sync --frozen --no-dev

# Копируем исходный код
COPY . .

# Устанавливаем браузеры для Playwright
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# Создаем директории для логов и временных файлов
RUN mkdir -p logs temp

# Открываем порт
EXPOSE 8000

# Переменные окружения по умолчанию
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

# Запускаем приложение
CMD ["uv", "run", "uvicorn", "main:create_fastapi_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
