# justfile
set dotenv-load := true
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]


# базовые параметры (можно переопределять: just dev HOST=0.0.0.0 PORT=8000)
HOST := env_var_or_default("HOST", "0.0.0.0")
PORT := env_var_or_default("PORT", "8000")

# локальный dev с автоперезапуском
dev:
    uv run uvicorn main:create_fastapi_app --factory --host {{HOST}} --port {{PORT}} --reload

# продовый запуск (без reload)
run:
    uv run uvicorn main:create_fastapi_app --factory --host {{HOST}} --port {{PORT}}

# CLI клиент (можно передавать аргументы: just cli ip --ip-number "123/45/67")
cli *args:
    uv run python -m src.infrastructure.cli {{args}}

# MCP server через stdio (стандартный режим)
mcp:
    uv run python mcp_server.py

# MCP server через HTTP (можно переопределять: just mcp-http MCP_HOST=127.0.0.1 MCP_PORT=8100)
MCP_HOST := env_var_or_default("MCP_HOST", "0.0.0.0")
MCP_PORT := env_var_or_default("MCP_PORT", "8100")
mcp-http:
    MCP_TRANSPORT=http uv run python mcp_server.py

# тесты
test:
    uv run pytest -v

# тесты с покрытием
test-cov:
    uv run pytest -v --cov=src --cov-report=term-missing --cov-report=html

# только unit-тесты
test-unit:
    uv run pytest -v tests/unit/

# только integration-тесты
test-integration:
    uv run pytest -v tests/integration/

# только e2e-тесты
test-e2e:
    uv run pytest -v tests/e2e/

# линтеры
lint:
    uv run ruff check src tests

# форматирование
fmt:
    uv run ruff format src tests

# проверка форматирования
fmt-check:
    uv run ruff format --check src tests

# полная проверка (линтинг + тесты)
check: lint test

# # запуск через Docker (если используете compose)
# dc-up:
#     docker compose up --build

# dc-down:
#     docker compose down