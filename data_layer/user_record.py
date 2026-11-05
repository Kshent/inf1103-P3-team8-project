# OOP - Aggregation: a UserRecord groups Search objects that were
# created elsewhere (see add_search).
# SOLID - SRP: UserRecord only groups one user's searches and owns the
# rule for which email belongs to which user.
class UserRecord:
    """All saved searches for one email address.

    Aggregation: a Search is created first (in DataManager) and then added
    with add_search(). The UserRecord does not create its searches; it only
    groups them under one email.
    """

    def __init__(self, email):
        # OOP - Encapsulation: private (__), the email is set once and the
        # searches can only change through add_search().
        self.__email = UserRecord.normalise_email(email)
        self.__searches = []

    # SOLID - SRP: the only place that decides how emails are matched, so
    # " Bob@Mail.com" and "bob@mail.com" are the same user. DataManager
    # uses this instead of repeating the rule.
    @staticmethod
    def normalise_email(email):
        return email.strip().lower()

    # OOP - Encapsulation: read-only property, the email cannot be changed
    # from outside.
    @property
    def email(self):
        return self.__email

    # OOP - Aggregation: receives a Search that already exists, instead of
    # creating it.
    def add_search(self, search):
        """Add a search; empty searches are ignored."""
        if not search.is_empty():
            self.__searches.append(search)

    def is_empty(self):
        return not self.__searches

    def to_dict(self):
        """Shape used by the IO Manager: {"email": ..., "searches": [[...]]}"""
        return {
            "email": self.__email,
            "searches": [search.hotels for search in self.__searches],
        }