import structlog
from twocaptcha import AsyncTwoCaptcha
from src.domain.errors import CaptchaError


logger = structlog.get_logger()


class CaptchaSolver:
    """Решатель капчи через внешний провайдер."""

    def __init__(self, api_key: str):
        self._solver = AsyncTwoCaptcha(api_key)

    async def solve(self, captcha_path) -> str:
        try:
            result = await self._solver.normal(str(captcha_path), numeric=1)
            code = result.get("code")
            if not code:
                raise CaptchaError("Провайдер капчи вернул пустой код")
            return str(code)
        except Exception as exc:  # noqa: BLE001
            logger.error("Ошибка распознавания капчи", error=exc)
            raise CaptchaError("Не удалось распознать капчу") from exc
