class Hotel:
    """One saved hotel. Keeps its own copy of the hotel dictionary and
    makes sure every field the IO Manager displays is present."""

    # Fields the IO Manager prints, with the value used when one is missing
    DEFAULTS = {
        "city": "Unknown",
        "country": "Unknown",
        "price_per_night_sgd": "N/A",
        "rating": "N/A",
        "amenities": [],
        "nearby_food": [],
        "nearby_activities": [],
    }

    def __init__(self, data):
        self._data = {**self.DEFAULTS, **data}

    @property
    def name(self):
        return str(self._data.get("name", "")).strip()

    def to_dict(self):
        return dict(self._data)
