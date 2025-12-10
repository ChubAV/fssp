from pydantic import BaseModel, RootModel, field_validator
import re
from datetime import datetime

def validate_inn(inn: str) -> str:
    if not re.fullmatch(r"\d{10}(\d{2})?", inn):
        raise ValueError("ИНН должен содержать 10 или 12 цифр")
    return inn


def validate_birthday(birthday: str) -> str:
    """Валидация даты рождения в формате DD.MM.YYYY"""
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", birthday):
        raise ValueError("Дата рождения должна быть в формате DD.MM.YYYY (например, 16.05.1992)")
    
    try:
        date_obj = datetime.strptime(birthday, "%d.%m.%Y")
        # Проверка, что дата не в будущем
        if date_obj > datetime.now():
            raise ValueError("Дата рождения не может быть в будущем")
        # Проверка разумного диапазона (не раньше 1900 года)
        if date_obj.year < 1900:
            raise ValueError("Дата рождения не может быть раньше 1900 года")
    except ValueError as e:
        if "time data" in str(e) or "unconverted data" in str(e):
            raise ValueError("Некорректная дата рождения")
        raise
    
    return birthday

def validate_ip_number(ip_number: str) -> str:
    if not re.fullmatch(r"^\d{1,7}/\d{2}/(?:\d{2,3}/\d{2}|\d{5}-(?:ИП|СД|СВ))$", ip_number):
        raise ValueError("Некорректный номер ИП/СД/СВ")
    return ip_number

class Person(BaseModel):
    """Модель для валидации данных о человеке"""
    last_name: str
    first_name: str
    patronymic: str | None = None
    birthday: str
    
    @field_validator("birthday")
    @classmethod
    def check_birthday(cls, v):
        return validate_birthday(v)


class Inn(BaseModel):
    """Модель для валидации данных по ИНН для юр лиц"""
    inn: str
    
    @field_validator("inn")
    @classmethod
    def check_inn(cls, v):
        return validate_inn(v)
    
    
class IpNumber(BaseModel):
    """Модель для валидации данных по ИП"""
    ip: str
    
    @field_validator("ip")
    @classmethod
    def check_ip(cls, v):
        return validate_ip_number(v)


class DebItem(BaseModel):
    """Схема элемента ИП"""
    region: str
    debtor: str
    ip: str
    doc: str
    end_reason: str | None = None
    debt: str
    office: str
    bailiff: str


class DebItemList(RootModel[list[DebItem]]):
    """Список элементов ИП"""
    root: list[DebItem]
    
class HealthcheckResponse(BaseModel):
    """Ответ на запрос healthcheck"""
    status: str