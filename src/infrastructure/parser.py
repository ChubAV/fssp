from bs4 import BeautifulSoup
import structlog
from src.domain.errors import ParsingError, CaptchaLimitExceeded


logger = structlog.get_logger()


class FsspHtmlParser:
    """Парсер HTML страницы результатов ФССП."""

    def parse_cases(self, html: str) -> list[dict]:
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:  # noqa: BLE001
            raise ParsingError("Не удалось распарсить HTML") from exc

        # Проверка на ошибку превышения лимита попыток капчи
        error_div = soup.select_one(".results .empty")
        if error_div:
            error_text = error_div.get_text(strip=True)
            if "Количество неверных попыток ввода кода превышено" in error_text:
                logger.warning("Обнаружено сообщение о превышении лимита попыток капчи")
                raise CaptchaLimitExceeded(
                    "Превышено количество неверных попыток ввода капчи. "
                    "Попробуйте позже или используйте другой способ получения данных."
                )

        table = soup.select_one(".results-frame table.list")
        if not table:
            logger.warning("Таблица результатов не найдена")
            return []

        current_region: str | None = None
        rows: list[dict] = []
        for tr in table.select("tr"):
            if tr.select("th"):
                continue
            if "region-title" in tr.get("class", []):
                current_region = tr.get_text(strip=True)
                continue

            tds = tr.select("td")
            if len(tds) != 8:
                continue

            rows.append(
                {
                    "region": current_region,
                    "debtor": " ".join(tds[0].stripped_strings),
                    "ip": " ".join(tds[1].stripped_strings),
                    "doc": " ".join(tds[2].stripped_strings),
                    "end_reason": " ".join(tds[3].stripped_strings),
                    "debt": " ".join(tds[5].stripped_strings),
                    "office": " ".join(tds[6].stripped_strings),
                    "bailiff": " ".join(tds[7].stripped_strings),
                }
            )

        return rows
