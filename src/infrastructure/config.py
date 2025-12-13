from pathlib import Path
from pydantic import Field, BaseModel, field_validator
from pydantic_settings import BaseSettings


def get_base_path() -> Path:
    # файл лежит в src/infrastructure, поэтому поднимаемся на два уровня до корня проекта
    return Path(__file__).resolve().parents[2]


def get_log_path() -> Path:
    return get_base_path() / "logs" / "main.log"


def get_temp_path() -> Path:
    return get_base_path() / "temp"


class BrowserConfig(BaseModel):
    headless: bool = True
    navigation_timeout_ms: int = 60000
    results_wait_ms: int = 5000
    user_agent: str | None = None
    captcha_selector: str = "img#capchaVisualImage"
    results_selector: str = ".results"
    screenshot_results: bool = True


class CaptchaConfig(BaseModel):
    api_key: str = Field(description="API ключ для RuCaptcha")
    temp_filename: str = "captcha.png"


class FsspUrls(BaseModel):
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
    PROJECT_NAME: str = "Микросервис поиска в ФССП (https://fssp.gov.ru/)"
    DEBUG: bool = False
    BASE_PATH: Path = Field(description="Путь к проекту", default_factory=get_base_path)
    LOG_PATH: Path = Field(description="Путь к логам", default_factory=get_log_path)
    HOST: str = Field(description="Хост", default="0.0.0.0")
    PORT: int = Field(description="Порт", default=8000)
    LOG_FILE_MAX_BYTES: int = Field(description="Максимальный размер файла лога", default=5 * 1024 * 1024)
    LOG_FILE_BACKUP_COUNT: int = Field(description="Количество копий файла лога", default=3)
    TEMP_PATH: Path = Field(description="Путь к временным файлам", default_factory=get_temp_path)
    RUCAPTCH_API_KEY: str = Field(description="API ключ для RuCaptcha")
    MCP_TRANSPORT: str = Field(description="Тип транспорта MCP: stdio или http", default="stdio")
    MCP_HOST: str = Field(description="Хост для HTTP транспорта MCP", default="0.0.0.0")
    MCP_PORT: int = Field(description="Порт для HTTP транспорта MCP", default=8100)

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    urls: FsspUrls = Field(default_factory=FsspUrls)
    captcha: CaptchaConfig | None = Field(default=None)

    class Config:
        env_file = ".env"

    @field_validator("TEMP_PATH")
    @classmethod
    def ensure_temp_exists(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("captcha", mode="before")
    @classmethod
    def populate_captcha(cls, v, info):
        if v is None:
            api_key = info.data.get("RUCAPTCH_API_KEY")
            if api_key:
                return {"api_key": api_key}
        return v


def create_settings() -> Settings:
    return Settings()
