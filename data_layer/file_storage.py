import os
import logging
from abc import abstractmethod

from data_layer.storage import Storage

logger = logging.getLogger(__name__)


class FileStorage(Storage):
    """Abstract base class for file storage.

    Handles the parts every file format shares: missing, empty, unreadable
    or corrupt files. Subclasses only say how to convert text <-> dict.
    """

    def __init__(self, path, file_type):
        self._path = path
        self._file_type = file_type

    @abstractmethod
    def _parse(self, text):
        """Convert file text into a dict."""

    @abstractmethod
    def _format(self, data):
        """Convert a dict into file text."""

    def read(self):
        if not os.path.exists(self._path):
            return {}

        try:
            with open(self._path, "r", encoding="utf-8") as file:
                content = file.read().strip()
            if not content:
                return {}
            data = self._parse(content)
        except (ValueError, OSError) as error:
            logger.error("Could not read %s file %s: %s",
                         self._file_type, self._path, error)
            return {}

        if not isinstance(data, dict):
            logger.error("%s file %s has an unexpected format.",
                         self._file_type, self._path)
            return {}

        return data

    def write(self, data):
        try:
            with open(self._path, "w", encoding="utf-8") as file:
                file.write(self._format(data))
            return True
        except OSError as error:
            logger.error("Could not save record to %s file %s: %s",
                         self._file_type, self._path, error)
            return False
