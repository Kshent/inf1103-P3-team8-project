from data_layer.search import Search
from data_layer.user_record import UserRecord

RECORDS_FILE = "datarecords.json"


class DataManager:
    """Saves, loads and queries hotel search records.

    Association: the DataManager is given a Storage object and uses it.
    It does not create or own the storage, and the storage is not a "part"
    of it; app.py decides which one to use.

    Polymorphism: it only calls read() and write(), so it works the same
    with a JsonStorage or a MemoryStorage, with no type checks.
    """

    def __init__(self, storage):
        self.__storage = storage


    def __load_users(self):
        """Turn the stored dict into UserRecord objects, keyed by email."""
        users = {}
        for email, searches in self.__storage.read().items():
            if not isinstance(searches, list):
                continue

            user = UserRecord(email)
            for hotels in searches:
                if isinstance(hotels, list):
                    search = Search(hotels)
                    user.add_search(search)

            if not user.is_empty():
                users[user.email] = user
        return users

    def __save_users(self, users):
        data = {user.email: user.to_dict()["searches"]
                for user in users.values()}
        # OOP - Polymorphism: write() saves to a file or to memory,
        # depending on which Storage object was passed in.
        return self.__storage.write(data)

    def save(self, record):
        """Add searches from {email: [hotel, ...]} to the stored records.

        Returns True if the records were written, False otherwise.
        """
        users = self.__load_users()

        for email, hotels in record.items():
            search = Search(hotels)
            key = UserRecord.normalise_email(email)
            if key not in users:
                users[key] = UserRecord(key)
            users[key].add_search(search)

        return self.__save_users(users)

    def load(self):
        """Return all records as [{"email": ..., "searches": [[...]]}]."""
        return [user.to_dict() for user in self.__load_users().values()]

    def query(self, record_email):
        """Return the records for one email, or [] if there are none."""
        if not record_email:
            return []
        # SOLID - SRP: the email rule lives in UserRecord, not here.
        user = self.__load_users().get(UserRecord.normalise_email(record_email))
        return [user.to_dict()] if user else []

    def query_by_country(self, record_email, country):
        """Return the records for one email, keeping only the hotels whose
        country contains the given text (not case sensitive, so "singa"
        finds Singapore). Returns [] if nothing matches."""
        if not record_email or not country:
            return []
        user = self.__load_users().get(UserRecord.normalise_email(record_email))
        if not user:
            return []
        record = user.to_dict_for_country(country)
        return [record] if record["searches"] else []