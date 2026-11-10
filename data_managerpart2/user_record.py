class UserRecord:
    """All saved searches for one email address.

    Aggregation: a Search is created first (in DataManager) and then added
    with add_search(). The UserRecord does not create its searches; it only
    groups them under one email.
    """

    def __init__(self, email):
        self.__email = UserRecord.normalise_email(email)
        self.__searches = []

    @staticmethod
    def normalise_email(email):
        return email.strip().lower()

    @property
    def email(self):
        return self.__email

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

    def to_dict_for_country(self, country_text):
        """Like to_dict(), but only with the hotels in a matching country.
        Searches with no matching hotel are left out."""
        searches = [search.hotels_in_country(country_text)
                    for search in self.__searches]
        return {
            "email": self.__email,
            "searches": [hotels for hotels in searches if hotels],
        }