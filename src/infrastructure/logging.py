import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import structlog


def setup_logging(
    level=logging.INFO,
    log_path: Path | None = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
):
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    handlers = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",  # structlog уже отрендерит JSON
        level=level,
        handlers=handlers,
    )
