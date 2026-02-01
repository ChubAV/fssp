"""HTTP-клиент для взаимодействия с сайтом ФССП через Playwright."""

from pathlib import Path
from playwright.async_api import TimeoutError, async_playwright, Page
import structlog

from src.infrastructure.config import BrowserConfig
from src.domain.errors import CaptchaError, FsspUnavailable, NetworkError
from src.domain.protocols import ICaptchaSolver


logger = structlog.get_logger()


class FsspClient:
    """Адаптер к веб-форме ФССП на Playwright."""

    def __init__(
        self,
        captcha_solver: ICaptchaSolver,
        browser_config: BrowserConfig,
        temp_path: Path,
    ):
        """
        Инициализация клиента ФССП.

        Args:
            captcha_solver: Сервис для распознавания капчи
            browser_config: Конфигурация браузера
            temp_path: Путь для временных файлов
        """
        self._captcha_solver = captcha_solver
        self._browser_config = browser_config
        self._temp_path = temp_path
        self._captcha_file = temp_path / "captcha.png"

    async def fetch(self, url: str) -> str:
        """
        Получить HTML результатов поиска с сайта ФССП.

        Args:
            url: URL для запроса

        Returns:
            HTML-строка с результатами

        Raises:
            FsspUnavailable: Сайт ФССП недоступен или вернул ошибку
            CaptchaError: Ошибка при решении капчи
            NetworkError: Сетевая ошибка
        """
        browser = None
        context = None
        page = None

        logger.debug("Открываем браузер для ФССП")
        async with async_playwright() as playwright:
            try:
                browser = await playwright.chromium.launch(
                    headless=self._browser_config.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(user_agent=self._browser_config.user_agent)
                page = await context.new_page()

                logger.debug("Переходим на страницу ФССП", url=url)
                response = await page.goto(
                    url,
                    timeout=self._browser_config.navigation_timeout_ms,
                    wait_until="domcontentloaded",
                )
                if response is None or (response.status is not None and response.status >= 400):
                    raise FsspUnavailable("Страница ФССП не открылась или вернула ошибку")

                await page.screenshot(path=self._temp_path / "fullpage1.png", full_page=True)

                logger.debug("Ждем капчу")
                img = await page.wait_for_selector(
                    self._browser_config.captcha_selector,
                    timeout=self._browser_config.navigation_timeout_ms,
                )
                if img is None:
                    raise CaptchaError("Капча не появилась на странице")

                logger.debug("Выключаем таймеры")
                # Это важный код. Он выключает обновление капчи, его убирать нельзя
                await page.evaluate("for (let i = 1; i < 99999; i++) clearInterval(i)")
                logger.debug("Делаем скриншот капчи")
                await img.screenshot(path=self._captcha_file)
                logger.debug("Решаем капчу с помощью RuCaptcha")
                captcha_code = await self._captcha_solver.solve(self._captcha_file)
                logger.debug("Распознанный код капчи", captcha_code=captcha_code)
                await page.locator("#captcha-popup-code").click()
                await page.locator("#captcha-popup-code").fill(str(captcha_code))
                await page.screenshot(path=self._temp_path / "fullpage2.png", full_page=True)
                await page.get_by_role("button", name="Отправить").click()

                logger.debug("Ждем результаты")
                results_ip = await page.wait_for_selector(
                    self._browser_config.results_selector,
                    timeout=self._browser_config.results_wait_ms,
                )
                await page.screenshot(path=self._temp_path / "fullpage3.png", full_page=True)
                html = await results_ip.inner_html()
                return html

            except CaptchaError:
                await self._save_error_screenshot(page)
                raise
            except FsspUnavailable:
                await self._save_error_screenshot(page)
                raise
            except TimeoutError as exc:
                await self._save_error_screenshot(page)
                raise NetworkError("Таймаут при работе с ФССП") from exc
            except Exception as exc:
                await self._save_error_screenshot(page)
                logger.error("Неожиданная ошибка при работе с ФССП", error=str(exc), error_type=type(exc).__name__)
                raise FsspUnavailable("Не удалось получить результаты из ФССП") from exc
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()

    async def _save_error_screenshot(self, page: Page | None) -> None:
        """
        Сохранить скриншот страницы при ошибке.

        Args:
            page: Объект страницы Playwright
        """
        if page:
            try:
                await page.screenshot(path=self._temp_path / "fullpage_error.png", full_page=True)
                logger.debug("Скриншот ошибки сохранен")
            except Exception as e:
                logger.warning("Не удалось сохранить скриншот ошибки", error=str(e))
