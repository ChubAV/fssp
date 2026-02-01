"""Конфигурация приложения."""

from pathlib import Path
from pydantic import Field, BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class BrowserConfig(BaseModel):
    """Конфигурация браузера для работы с Playwright."""

    headless: bool = True
    navigation_timeout_ms: int = 60000
    results_wait_ms: int = 5000
    user_agent: str | None = None
    captcha_selector: str = "img#capchaVisualImage"
    results_selector: str = ".results"
    screenshot_results: bool = True


class FsspUrls(BaseModel):
    """URL-шаблоны для запросов к ФССП."""

    ip: str = Field(
        description="URL ФССП для получения данных по ИП",
        default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=3&is%5Bip_number%5D={ip_number}",
    )
    person: str = Field(
        description="URL ФССП для получения данных по ФИО",
        default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=1&is%5Blast_name%5D={last_name}&is%5Bfirst_name%5D={first_name}&is%5Bpatronymic%5D={patronymic}&is%5Bdate%5D={birthday}&is%5Bregion_id%5D%5B0%5D={region_id}",
    )
    inn: str = Field(
        description="URL ФССП для получения данных по ИНН",
        default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=5&is%5Binn%5D={inn}",
    )


class Settings(BaseSettings):
    """Основные настройки приложения."""

    PROJECT_NAME: str = "Микросервис поиска в ФССП (https://fssp.gov.ru/)"
    DEBUG: bool = False
    HOST: str = Field(description="Хост", default="0.0.0.0")
    PORT: int = Field(description="Порт", default=8000)
    LOG_FILE_MAX_BYTES: int = Field(description="Максимальный размер файла лога", default=5 * 1024 * 1024)
    LOG_FILE_BACKUP_COUNT: int = Field(description="Количество копий файла лога", default=3)
    RUCAPTCH_API_KEY: str = Field(description="API ключ для RuCaptcha")
    MCP_TRANSPORT: str = Field(description="Тип транспорта MCP: stdio или http", default="stdio")
    MCP_HOST: str = Field(description="Хост для HTTP транспорта MCP", default="0.0.0.0")
    MCP_PORT: int = Field(description="Порт для HTTP транспорта MCP", default=8100)

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    urls: FsspUrls = Field(default_factory=FsspUrls)

    model_config = ConfigDict(env_file=".env")

    @property
    def base_path(self) -> Path:
        """Путь к корню проекта."""
        # файл лежит в src/infrastructure, поднимаемся на два уровня
        return Path(__file__).resolve().parents[2]

    @property
    def log_path(self) -> Path:
        """Путь к файлу логов."""
        return self.base_path / "logs" / "main.log"

    @property
    def temp_path(self) -> Path:
        """Путь к временным файлам."""
        path = self.base_path / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def database_path(self) -> Path:
        """Путь к файлу базы данных задач."""
        return self.base_path / "tasks.db"


def create_settings() -> Settings:
    """Создать экземпляр настроек приложения."""
    return Settings()
