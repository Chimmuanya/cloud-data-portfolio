"""
src/common/logging.py

Standard logging configuration for Project 3.
"""

import logging
import os

# Detect if we are in Lambda to adjust formatting
IS_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
DEFAULT_LEVEL_STR = os.environ.get("LOG_LEVEL", "INFO").upper()

def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    # Validate Log Level
    level = getattr(logging, DEFAULT_LEVEL_STR, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    logger.setLevel(level)
    handler = logging.StreamHandler()

    # CLOUD FIX: Remove asctime if in Lambda because CloudWatch adds it automatically
    if IS_LAMBDA:
        log_format = "%(levelname)s | %(name)s | %(message)s"
    else:
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
