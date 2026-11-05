from data_layer.hotel import Hotel


class Search:
    """One saved hotel search (the top hotels returned for it).

    Composition: the Search creates its own Hotel objects, so the hotels
    are created and destroyed together with the search.
    """

    def __init__(self, hotel_dicts):
        hotels = [Hotel(data) for data in hotel_dicts if isinstance(data, dict)]
        # A hotel without a name cannot be shown to the user, so drop it
        self.__hotels = [hotel for hotel in hotels if hotel.name]

    @property
    def hotels(self):
        return [hotel.to_dict() for hotel in self.__hotels]

    def is_empty(self):
        return not self.__hotels
