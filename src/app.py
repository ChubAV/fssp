from fastapi import FastAPI
from src.config import Settings
from src.api import router as api_router
from src.middleware import add_request_context

def create_app(settings: Settings):
    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)
    app.middleware("http")(add_request_context)
    app.include_router(api_router, prefix="/api")
    app.settings = settings
    return app