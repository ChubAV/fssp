import time

import structlog
from fastapi import Request


logger = structlog.get_logger()


async def add_request_context(request: Request, call_next):
    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("x-request-id", "unknown"),
        path=str(request.url.path),
        method=request.method,
    )
    started_at = time.monotonic()
    try:
        logger.info("Запрос отправлен на обработку")
        response = await call_next(request)
        duration_ms = round((time.monotonic() - started_at) * 1000, 2)
        logger.info("Запрос обработан", duration_ms=duration_ms, status_code=response.status_code)
        return response
    except Exception as exc:  # noqa: BLE001
        duration_ms = round((time.monotonic() - started_at) * 1000, 2)
        logger.error("Ошибка обработки запроса", duration_ms=duration_ms, error=str(exc))
        raise
    finally:
        structlog.contextvars.clear_contextvars()





