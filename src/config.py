from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

def get_base_path():
    return Path(__file__).parent.parent

def get_log_path():
    return get_base_path() / "logs" / "main.log"

def get_temp_path():
    return get_base_path() / "temp"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Микросервис поиска в ФССП (https://fssp.gov.ru/)"
    DEBUG: bool = False
    BASE_PATH: Path = Field(description='Путь к проекту', default_factory=get_base_path)
    LOG_PATH: Path = Field(description='Путь к логам', default_factory=get_log_path)
    HOST: str = Field(description='Хост', default="0.0.0.0")
    PORT: int = Field(description='Порт', default=8000)
    LOG_FILE_MAX_BYTES: int = Field(description='Максимальный размер файла лога', default=5 * 1024 * 1024)
    LOG_FILE_BACKUP_COUNT: int = Field(description='Количество копий файла лога', default=3)
    TEMP_PATH: Path = Field(description='Путь к временным файлам', default_factory=get_temp_path)
    RUCAPTCH_API_KEY: str = Field(description='API ключ для RuCaptcha')
    URL_FSSP_IP: str = Field(description='URL ФССП для получения данных по ИП', default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=3&is%5Bip_number%5D={ip_number}")
    URL_FSSP_PERSON: str = Field(description='URL ФССП для получения данных по ФИО', default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=1&is%5Blast_name%5D={last_name}&is%5Bfirst_name%5D={first_name}&is%5Bpatronymic%5D={patronymic}&is%5Bdate%5D={birthday}&is%5Bregion_id%5D%5B0%5D={region_id}")
    URL_FSSP_INN: str = Field(description='URL ФССП для получения данных по ИНН', default="https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=5&is%5Binn%5D={inn}")
    
    class Config:
        env_file = ".env"
        



def create_settings():
    return Settings()


