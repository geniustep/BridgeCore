"""
Advanced Logging Configuration using Loguru
"""
from loguru import logger
import sys
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """
    Setup advanced logging system with Loguru

    Features:
    - Console logging (for development)
    - File logging (all levels)
    - Error-only logging
    - JSON logging (for production)
    """
    # Remove default handler
    logger.remove()

    # Console logging (for Development)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # File logging (all levels)
    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=settings.LOG_ROTATION,  # "10 MB"
        retention="30 days",
        compression="zip",
        enqueue=True  # Async logging
    )

    # Error logging (errors only)
    logger.add(
        log_path.parent / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        backtrace=True,
        diagnose=True
    )

    # JSON logging (for Production - easier parsing)
    if settings.ENVIRONMENT == "production":
        logger.add(
            log_path.parent / "app.json",
            format="{message}",
            level="INFO",
            rotation="100 MB",
            serialize=True  # JSON format
        )

    logger.info("Logging system initialized")
