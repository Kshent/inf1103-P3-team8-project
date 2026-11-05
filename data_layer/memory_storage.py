import json
import copy


from data_layer.storage import Storage


class MemoryStorage(Storage):
    """Keeps records in memory only. Useful for tests (no file needed)."""

    def __init__(self):
        self.__data = {}

    def read(self):
        return copy.deepcopy(self.__data)

    def write(self, data):
        try:
            self.__data = copy.deepcopy(data)
            return True
        except (TypeError, copy.Error):
            return False
