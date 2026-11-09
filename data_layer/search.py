from data_layer.hotel import Hotel


class Search:
    """One saved hotel search (the top hotels returned for it).

    Composition: the Search receives plain dicts and creates its own Hotel
    objects from them. The Hotel objects are never handed out (only copies
    of their data), so they are created and destroyed with the Search.
    """

    def __init__(self, hotel_dicts):
        hotels = [Hotel(data) for data in hotel_dicts if isinstance(data, dict)]
        self.__hotels = [hotel for hotel in hotels if hotel.name]

    @property
    def hotels(self):
        return [hotel.to_dict() for hotel in self.__hotels]

    def hotels_in_country(self, country_text):
        """Copies of the hotels whose country matches the text."""
        return [hotel.to_dict() for hotel in self.__hotels
                if hotel.is_in_country(country_text)]

    def is_empty(self):
        return not self.__hotels
