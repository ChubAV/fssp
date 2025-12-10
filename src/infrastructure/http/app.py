from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.infrastructure.config import Settings
from src.domain.errors import DomainError, CaptchaLimitExceeded

from .api import router as api_router
from .middleware import add_request_context


def create_app(settings: Settings):
    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)
    app.middleware("http")(add_request_context)
    app.include_router(api_router, prefix="/api")
    app.settings = settings

    @app.exception_handler(CaptchaLimitExceeded)
    async def captcha_limit_handler(request: Request, exc: CaptchaLimitExceeded):  # noqa: WPS430
        return JSONResponse(
            status_code=429,
            content={"detail": str(exc), "error_code": "CAPTCHA_LIMIT_EXCEEDED"}
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):  # noqa: WPS430
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app
