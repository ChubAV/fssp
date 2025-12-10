from fastapi import Request
from src.config import Settings

def get_settings(request: Request) -> Settings:
    return request.app.settings