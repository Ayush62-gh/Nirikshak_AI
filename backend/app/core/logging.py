import logging
import sys
from typing import Any, Dict
from app.core.config import settings


class Formatter(logging.Formatter):
    """Clean structured log formatter with timestamp, level, and component metadata."""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.format_str)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> logging.Logger:
    """Configure root and application loggers."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Root logger
    logger = logging.getLogger("nirikshak")
    logger.setLevel(log_level)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(Formatter())
        logger.addHandler(console_handler)

    # Suppress verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
