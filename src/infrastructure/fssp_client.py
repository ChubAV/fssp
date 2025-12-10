from pathlib import Path
from playwright.async_api import TimeoutError, async_playwright
import structlog

from src.infrastructure.config import Settings
from src.domain.errors import CaptchaError, FsspUnavailable
from src.infrastructure.captcha import CaptchaSolver


logger = structlog.get_logger()


class FsspClient:
    """Адаптер к веб-форме ФССП на Playwright."""

    def __init__(self, captcha_solver: CaptchaSolver):
        self._captcha_solver = captcha_solver

    async def fetch(self, url: str, settings: Settings) -> str:
        browser_cfg = settings.browser
        captcha_cfg = settings.captcha
        temp_path: Path = settings.TEMP_PATH
        captcha_file = temp_path / (captcha_cfg.temp_filename if captcha_cfg else "captcha.png")
        browser = None
        context = None
        page = None

        logger.debug("Открываем браузер для ФССП")
        async with async_playwright() as playwright:
            try:
                browser = await playwright.chromium.launch(
                    headless=browser_cfg.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(user_agent=browser_cfg.user_agent)
                page = await context.new_page()

                logger.debug("Переходим на страницу ФССП", url=url)
                response = await page.goto(
                    url,
                    timeout=browser_cfg.navigation_timeout_ms,
                    wait_until="domcontentloaded",
                )
                if response is None or (response.status is not None and response.status >= 400):
                    raise FsspUnavailable("Страница ФССП не открылась или вернула ошибку")
               
                await page.screenshot(path=temp_path / "fullpage1.png", full_page=True)

                logger.debug("Ждем капчу")
                img = await page.wait_for_selector(
                    browser_cfg.captcha_selector,
                    timeout=browser_cfg.navigation_timeout_ms,
                )
                if img is None:
                    raise CaptchaError("Капча не появилась на странице")

                logger.debug("Выключаем таймеры")
                await page.evaluate("for (let i = 1; i < 99999; i++) clearInterval(i)") # это важный код. он выключает обновление капчи его убирать нельзя
                logger.debug("Делаем скриншот капчи")
                await img.screenshot(path=captcha_file)
                logger.debug("Решаем капчу с помощью RuCaptcha")
                captcha_code = await self._captcha_solver.solve(captcha_file)
                logger.debug("Распознанный код капчи", captcha_code=captcha_code)
                await page.locator("#captcha-popup-code").click()
                await page.locator("#captcha-popup-code").fill(str(captcha_code))
                await page.screenshot(path=temp_path / "fullpage2.png", full_page=True)
                await page.get_by_role("button", name="Отправить").click()

                logger.debug("Ждем результаты")
                results_ip = await page.wait_for_selector(browser_cfg.results_selector, timeout=browser_cfg.results_wait_ms)
                await page.screenshot(path=temp_path / "fullpage3.png", full_page=True)
                html = await results_ip.inner_html()
            except CaptchaError:
                if page:
                    await page.screenshot(path=temp_path / "fullpage_error.png", full_page=True)
                raise
            except FsspUnavailable:
                if page:
                    await page.screenshot(path=temp_path / "fullpage_error.png", full_page=True)
                raise
            except TimeoutError as exc:
                if page:
                    await page.screenshot(path=temp_path / "fullpage_error.png", full_page=True)
                raise FsspUnavailable("Таймаут при работе с ФССП") from exc
            except Exception as exc:  # noqa: BLE001
                if page:
                    await page.screenshot(path=temp_path / "fullpage_error.png", full_page=True)
                raise FsspUnavailable("Не удалось получить результаты из ФССП") from exc
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()

        return html
