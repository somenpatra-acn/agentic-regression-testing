"""Logging configuration and utilities."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import get_settings


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None) -> None:
    """
    Configure logging for the application.

    Args:
        log_file: Path to log file (uses settings if not provided)
        log_level: Log level (uses settings if not provided)
    """
    settings = get_settings()
    log_file = log_file or settings.log_file
    log_level = log_level or settings.log_level

    # Remove default handler
    logger.remove()

    # Console handler with rich formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File handler with detailed information
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # Always capture DEBUG in file
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)


# Initialize logging on import
try:
    setup_logging()
except Exception as e:
    print(f"Warning: Could not initialize logging: {e}")
    logger.warning(f"Logging initialization failed: {e}")
