import copy


class Hotel:
    """One saved hotel. Keeps its own copy of the hotel dictionary and
    makes sure every field the IO Manager displays is present."""

    __DEFAULTS = {
        "city": "Unknown",
        "country": "Unknown",
        "price_per_night_sgd": "N/A",
        "rating": "N/A",
        "amenities": [],
        "nearby_food": [],
        "nearby_activities": [],
    }

    def __init__(self, data):
        self.__data = dict(data)
        for field, default in self.__DEFAULTS.items():
            if field not in self.__data:
                self.__data[field] = copy.copy(default)

    @property
    def name(self):
        return str(self.__data.get("name", "")).strip()

    @property
    def country(self):
        return str(self.__data.get("country", "")).strip()

    @staticmethod
    def normalise_country(text):
        return " ".join(str(text).lower().split())

    def is_in_country(self, country_text):
        """True if the hotel's country contains the text, not case
        sensitive, so "singa" matches "Singapore"."""
        wanted = Hotel.normalise_country(country_text)
        return bool(wanted) and wanted in Hotel.normalise_country(self.country)

    def to_dict(self):
        return dict(self.__data)