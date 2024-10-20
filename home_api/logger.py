import logging
import os
from .etc import LOGS_DIR, LOG_FILENAME, NOW

logger = logging.getLogger("uvicorn.error")


def init_logger():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)
    filepath = os.path.join(LOGS_DIR, LOG_FILENAME)
    file_handler = logging.FileHandler(filepath)
    logger.addHandler(file_handler)
    logger.info(f"API started at {NOW}")


__all__ = ["init_logger", "logger"]
