# In task_assistant/logger_config.py

import logging
import sys


def setup_logger():
    """Sets up a configured logger."""

    # Create logger
    logger = logging.getLogger("TaskMasterAI")
    logger.setLevel(logging.INFO)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    # Return logger if it's already configured
    if logger.hasHandlers():
        return logger

    # Define log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create a single logger instance to be used across the application
log = setup_logger()