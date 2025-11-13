"""Logging configuration for HiyaDrive."""

import sys
from pathlib import Path
from loguru import logger as loguru_logger
from hiya_drive.config.settings import settings


def setup_logger():
    """Configure loguru for HiyaDrive."""

    # Remove default handler
    loguru_logger.remove()

    # Console output with color
    loguru_logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # File output (logs directory)
    log_file = settings.logs_dir / f"hiya_drive_{settings.app_env}.log"
    loguru_logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="500 MB",
        retention="7 days",
    )

    # Error log file
    error_log_file = settings.logs_dir / f"hiya_drive_errors_{settings.app_env}.log"
    loguru_logger.add(
        str(error_log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="500 MB",
        retention="30 days",
    )

    return loguru_logger


# Initialize logger on module import
logger = setup_logger()
