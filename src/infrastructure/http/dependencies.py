from fastapi import Request

from src.application.fssp_service import FsspService
from src.infrastructure.config import Settings
from src.infrastructure.captcha import CaptchaSolver
from src.infrastructure.fssp_client import FsspClient
from src.infrastructure.parser import FsspHtmlParser


def get_settings(request: Request) -> Settings:
    return request.app.settings


def _build_fssp_service(settings: Settings) -> FsspService:
    captcha_solver = CaptchaSolver(api_key=settings.captcha.api_key if settings.captcha else settings.RUCAPTCH_API_KEY)
    client = FsspClient(captcha_solver=captcha_solver)
    parser = FsspHtmlParser()
    return FsspService(settings=settings, client=client, parser=parser)


def get_fssp_service(request: Request) -> FsspService:
    service = getattr(request.app.state, "fssp_service", None)
    if service:
        return service
    settings = get_settings(request)
    service = _build_fssp_service(settings)
    request.app.state.fssp_service = service
    return service
