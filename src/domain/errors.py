"""Доменные ошибки приложения."""


class DomainError(Exception):
    """Базовая доменная ошибка."""


class RetryableError(DomainError):
    """Базовая ошибка, при которой имеет смысл повторить операцию."""


class NetworkError(RetryableError):
    """Сетевая ошибка (таймаут, недоступность хоста и т.п.)."""


class TemporaryCaptchaError(RetryableError):
    """Временная ошибка при распознавании капчи (может быть повторена)."""


class CaptchaError(DomainError):
    """Ошибка при распознавании капчи (критическая, не повторяется)."""


class CaptchaLimitExceeded(DomainError):
    """Превышено количество неверных попыток ввода капчи."""


class ParsingError(DomainError):
    """Ошибка при парсинге ответа ФССП."""


class ValidationError(DomainError):
    """Ошибка валидации входных данных."""


class FsspUnavailable(RetryableError):
    """Сервис ФССП недоступен или вернул пустой ответ."""
