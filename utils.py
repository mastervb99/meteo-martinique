"""
Utility functions for Martinique Weather Dashboard.

Includes logging configuration and helper functions.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: bool = True,
    log_dir: Optional[Path] = None,
    name: str = "martinique_weather",
) -> logging.Logger:
    """
    Configure logging with console and optional file output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Whether to also log to a file
        log_dir: Directory for log files (default: ./logs)
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    if log_file:
        if log_dir is None:
            log_dir = Path(__file__).parent / "logs"

        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"run_{timestamp}.log"

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        logger.debug(f"Log file: {log_path}")

    logger.propagate = False
    return logger


def get_logger(name: str = "martinique_weather") -> logging.Logger:
    """Get existing logger or create basic one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class LogContext:
    """Context manager for logging block execution with timing."""

    def __init__(self, logger: logging.Logger, message: str):
        self.logger = logger
        self.message = message
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"{self.message}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"{self.message}... done ({duration:.2f}s)")
        else:
            self.logger.error(f"{self.message}... failed ({duration:.2f}s): {exc_val}")
        return False
