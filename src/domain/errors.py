class DomainError(Exception):
    """Базовая доменная ошибка."""


class CaptchaError(DomainError):
    """Ошибка при распознавании капчи."""


class ParsingError(DomainError):
    """Ошибка при парсинге ответа ФССП."""


class FsspUnavailable(DomainError):
    """Сервис ФССП недоступен или вернул пустой ответ."""
