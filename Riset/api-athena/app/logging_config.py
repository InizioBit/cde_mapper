from __future__ import annotations

import logging
import sys

from app.config import get_settings


LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "%(message)s"
)


def configure_logging() -> None:
    settings = get_settings()
    settings.log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.log_level)

    file_handler = logging.FileHandler(settings.log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.log_level)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
