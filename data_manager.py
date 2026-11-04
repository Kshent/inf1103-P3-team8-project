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
            #new change to handle empty file, if the file is empty, return empty dict
            content = file.read().strip()

            if not content:
                return {}
            
            data = json.loads(content)
            ##
    except (json.JSONDecodeError, OSError) as error:
        logger.error("Could not read %s: %s", RECORDS_FILE, error)
        return {}

    if not isinstance(data, dict):
        logger.error("%s has an unexpected format.", RECORDS_FILE)
        return {}

    return data



def save(record):

    records = _read_file()

    #append the recent records into existing email if have, if not append
    #to empty list
    for email, hotels in record.items():
        email = email.strip().lower()
        records.setdefault(email, []).append(hotels)

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
        {"email": email, "searches": searches}
        for email, searches in records.items()
    ]


def query(record_email):

    hotels = _read_file().get(record_email)

    if hotels is None:
        return []

    return [{"email": record_email, "searches": hotels}]


class JsonRecordRepository:
    """Repository adapter that retains the existing JSON records format."""

    def save(self, email, hotels):
        save({email: hotels})

    def find_by_email(self, email):
        return query(email.strip().lower())

    def find_all(self):
        return load()


class JsonProfileRepository:
    """Persist traveller scoring profiles separately from hotel records."""

    def __init__(self, path="profiles.json"):
        self._path = path

    def _read_profiles(self):
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            logger.error("Could not read profiles from %s: %s",
                         self._path, error)
            return {}
        if not isinstance(profiles, dict):
            logger.error("%s has an unexpected format.", self._path)
            return {}
        return profiles

    def load_profile(self, email):
        return self._read_profiles().get(email.strip().lower())

    def save_profile(self, email, profile):
        profiles = self._read_profiles()
        profiles[email.strip().lower()] = profile
        try:
            with open(self._path, "w", encoding="utf-8") as file:
                json.dump(profiles, file, indent=4, ensure_ascii=False)
        except OSError as error:
            logger.error("Could not save profile to %s: %s",
                         self._path, error)