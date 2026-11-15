from __future__ import annotations

import logging
import os

from .ai_config import AIConfig
from .ai_logger import AILogger


class AIErrorLogger(AILogger):
    """File-backed AILogger. Owns and configures its own logging.Logger."""

    LOGGER_NAME = "ai_manager"

    def __init__(self, log_file: str = AIConfig.AI_ERROR_LOG_FILE):
        log_directory = os.path.dirname(log_file)
        if log_directory:
            os.makedirs(log_directory, exist_ok=True)

        self.__logger = logging.getLogger(self.LOGGER_NAME)
        self.__logger.setLevel(logging.WARNING)
        self.__logger.propagate = False

        if not self.__logger.handlers:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            )
            self.__logger.addHandler(file_handler)

    def warning(self, message: str, *args) -> None:
        self.__logger.warning(message, *args)

    def error(self, message: str, *args) -> None:
        self.__logger.error(message, *args)
