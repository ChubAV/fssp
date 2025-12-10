from fastapi import Request
import structlog


logger = structlog.get_logger()

async def add_request_context(request: Request, call_next):
    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("x-request-id", "unknown"),
        path=str(request.url.path),
        method=request.method,
    )
    try:
        logger.info('Запрос отправлен на обработку')
        response = await call_next(request)
        logger.info('Запрос обработан')
        
        return response
    finally:
        structlog.contextvars.clear_contextvars()