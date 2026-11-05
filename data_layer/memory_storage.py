import json

from data_layer.storage import Storage


class MemoryStorage(Storage):
    """Keeps records in memory only. Useful for tests (no file needed)."""

    def __init__(self):
        self._data = {}

    def read(self):
        return json.loads(json.dumps(self._data))

    def write(self, data):
        self._data = json.loads(json.dumps(data))
        return True
