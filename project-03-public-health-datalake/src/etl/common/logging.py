"""
src/common/logging.py

Standard logging configuration for Project 3.
"""

import logging
import os


DEFAULT_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging(name: str) -> logging.Logger:
    """
    Create a configured logger.

    Usage:
        logger = setup_logging(__name__)
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Prevent duplicate handlers (important for Lambda)
        return logger

    level = getattr(logging, DEFAULT_LEVEL, logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
