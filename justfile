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

# # тесты (пример, подставьте свои команды)
# test:
#     pytest -q

# # линтеры (пример, подставьте свои)
# lint:
#     ruff check src
# fmt:
#     ruff format src

# # запуск через Docker (если используете compose)
# dc-up:
#     docker compose up --build

# dc-down:
#     docker compose down