# import os
# import logging
# from abc import abstractmethod

# from data_layer.storage import Storage

# logger = logging.getLogger(__name__)


# class FileStorage(Storage):
#     """Abstract base class for file storage.

#     Handles the parts every file format shares: missing, empty, unreadable
#     or corrupt files. Subclasses only say how to convert text <-> dict.
#     """

#     def __init__(self, path, file_type):
#         self.__path = path
#         self.__file_type = file_type

#     @abstractmethod
#     def _parse(self, text):
#         """Convert file text into a dict."""

#     @abstractmethod
#     def _format(self, data):
#         """Convert a dict into file text."""

#     def read(self):
#         if not os.path.exists(self.__path):
#             return {}

#         try:
#             with open(self.__path, "r", encoding="utf-8") as file:
#                 content = file.read().strip()
#             if not content:
#                 return {}
#             data = self._parse(content)
#         except (ValueError, OSError) as error:
#             logger.error("Could not read %s file %s: %s",
#                          self.__file_type, self.__path, error)
#             return {}

#         if not isinstance(data, dict):
#             logger.error("%s file %s has an unexpected format.",
#                          self.__file_type, self.__path)
#             return {}

#         return data

#     def write(self, data):
#         try:
#             with open(self.__path, "w", encoding="utf-8") as file:
#                 file.write(self.__format(data))
#             return True
#         except OSError as error:
#             logger.error("Could not save record to %s file %s: %s",
#                          self.__file_type, self.__path, error)
#             return False


import os
import logging
from abc import abstractmethod

from data_layer.storage import Storage

logger = logging.getLogger(__name__)


class FileStorage(Storage):
    """Abstract base class for storing records in a file.

    Shared behaviour: read() and write() handle the parts every file format
    has in common (missing, empty, unreadable or corrupt files, and write
    errors). Abstract operations: subclasses only say how to turn file text
    into a dict (_parse) and a dict into file text (_format).
    """

    def __init__(self, path, file_type):
        self.__path = path
        self.__file_type = file_type

    @abstractmethod
    def _parse(self, text):
        """Convert file text into a dict.

        SOLID - LSP: raise ValueError if the text is not valid, so read()
        can catch it and keep the Storage promise of never raising.
        """

    @abstractmethod
    def _format(self, data):
        """Convert a dict into file text.

        SOLID - LSP: raise TypeError or ValueError if the data cannot be
        written, so write() can catch it and return False.
        """

    def read(self):
        if not os.path.exists(self.__path):
            return {}

        try:
            with open(self.__path, "r", encoding="utf-8") as file:
                content = file.read().strip()
            if not content:
                return {}
            data = self._parse(content)
        except (ValueError, OSError) as error:
            logger.error("Could not read %s file %s: %s",
                         self.__file_type, self.__path, error)
            return {}

        if not isinstance(data, dict):
            logger.error("%s file %s has an unexpected format.",
                         self.__file_type, self.__path)
            return {}

        return data

    def write(self, data):
        try:
            text = self._format(data)
            with open(self.__path, "w", encoding="utf-8") as file:
                file.write(text)
            return True
        except (TypeError, ValueError, OSError) as error:
            logger.error("Could not save record to %s file %s: %s",
                         self.__file_type, self.__path, error)
            return False