"""
Logging Configuration Module for TracerTemplateMaker

Sets up structured logging to console and file.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name="TracerTemplateMaker"):
    """
    Configure and return a logger instance.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Check if handlers are already added to avoid duplicates
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = os.path.join(os.path.expanduser("~"), ".tracertemplatemaker", "logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            # Fallback to local directory if cannot create in home
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    # Rotating file handler (max 1MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
