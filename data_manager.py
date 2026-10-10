import os
import json
import logging

logger = logging.getLogger(__name__)

RECORDS_FILE = "datarecords.json"


def _read_file():
    """Read the raw {uuid: record} dict from the file.
    Returns {} if the file is missing, unreadable or corrupt."""
    if not os.path.exists(RECORDS_FILE):
        return {}

    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        logger.error("Could not read %s: %s", RECORDS_FILE, error)
        return {}

    if not isinstance(data, dict):
        logger.error("%s has an unexpected format.", RECORDS_FILE)
        return {}

    return data


def save(record):
    """Append a processed record, shaped like {uuid: {...}}, to the file."""
    records = _read_file()
    records.update(record)

    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)
    except OSError as error:
        logger.error("Could not save record: %s", error)


def load():
    """Return all records as a list of dicts.
    Returns [] if the file does not exist or is corrupt. Never crashes."""
    records = _read_file()

    
    return [
        {"id": record_id, "hotels": hotels}
        for record_id, hotels in records.items()
    ]


def query(record_id):

    hotels = _read_file().get(record_id)

    if hotels is None:
        return []

    return [{"id": record_id, "hotels": hotels}]