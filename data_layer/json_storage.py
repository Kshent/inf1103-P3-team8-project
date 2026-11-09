# import json

# from data_layer.file_storage import FileStorage


# class JsonStorage(FileStorage):
#     """Stores records in a JSON file."""

#     def __init__(self, path):
#         # Pass the file path and file type up to FileStorage
#         super().__init__(path, "JSON")

#     def _parse(self, text):
#         return json.loads(text)

#     def _format(self, data):
#         return json.dumps(data, indent=4, ensure_ascii=False)

import json

from data_layer.file_storage import FileStorage


class JsonStorage(FileStorage):
    """Stores records in a JSON file.

    Inheritance: JsonStorage IS-A FileStorage. It reuses read() and write()
    and provides its own JSON parsing and formatting.
    """

    def __init__(self, path):
        super().__init__(path, "JSON")

    def _parse(self, text):
        return json.loads(text)

    def _format(self, data):
        return json.dumps(data, indent=4, ensure_ascii=False)