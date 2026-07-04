"""
logger.py
Centralized logging setup using loguru. Import get_logger(name) anywhere.
"""

import sys
from pathlib import Path
from loguru import logger
from config import LOGS_DIR

logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> - {message}",
    level="INFO",
)

logger.add(
    Path(LOGS_DIR) / "findoc_ai.log",
    rotation="5 MB",
    retention="10 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
)


def get_logger(name: str):
    return logger.bind(name=name)