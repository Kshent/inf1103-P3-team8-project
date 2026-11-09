import copy

from data_layer.storage import Storage


class MemoryStorage(Storage):
    """Keeps records in memory only, so nothing is saved after the app
    closes. Used for demos (DATA_STORAGE=memory) and for tests that should
    not touch the real records file.
    """

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