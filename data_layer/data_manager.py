from data_layer.search import Search
from data_layer.user_record import UserRecord

RECORDS_FILE = "datarecords.json"


# OOP - Classes and objects: app.py creates one DataManager object and
# uses it for every save, view and admin request.
# SOLID - SRP: DataManager only coordinates saving, loading and querying
# records. Reading/writing is done by Storage, the email rule by
# UserRecord, and checking hotels by Search/Hotel.
# SOLID - OCP: it only depends on the Storage interface, so a new storage
# type (e.g. a database) can be added without changing this class.
class DataManager:
    """Saves, loads and queries hotel search records.

    Association: the DataManager is given a Storage object and uses it.
    It does not create or own the storage, and the storage is not a "part"
    of it; app.py decides which one to use.

    Polymorphism: it only calls read() and write(), so it works the same
    with a JsonStorage or a MemoryStorage, with no type checks.
    """

    def __init__(self, storage):
        # OOP - Association: the storage is created in app.py and passed in.
        # DataManager only keeps a reference to it and uses it.
        # OOP - Encapsulation: private (__), only DataManager uses it.
        # SOLID - LSP: any Storage can be passed in (JsonStorage or
        # MemoryStorage) and DataManager behaves correctly with each.
        self.__storage = storage

    # OOP - Encapsulation: private helper, not part of the public interface.
    def __load_users(self):
        """Turn the stored dict into UserRecord objects, keyed by email."""
        users = {}
        # OOP - Polymorphism: read() runs JsonStorage or MemoryStorage
        # behaviour depending on the object passed in, with no type checks.
        for email, searches in self.__storage.read().items():
            if not isinstance(searches, list):
                continue
            # OOP - Classes and objects: a UserRecord object per email.
            user = UserRecord(email)
            for hotels in searches:
                if isinstance(hotels, list):
                    # OOP - Aggregation: the Search is created here, then
                    # added to the UserRecord.
                    search = Search(hotels)
                    user.add_search(search)
            # Skip users whose saved searches were all unreadable
            if not user.is_empty():
                users[user.email] = user
        return users

    # OOP - Encapsulation: private helper, not part of the public interface.
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
            # OOP - Aggregation: the Search is built on its own first,
            # so it exists before it becomes part of a UserRecord.
            search = Search(hotels)
            # SOLID - SRP: the email rule lives in UserRecord, not here.
            key = UserRecord.normalise_email(email)
            if key not in users:
                users[key] = UserRecord(key)
            # OOP - Aggregation: the existing Search is added to the user.
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