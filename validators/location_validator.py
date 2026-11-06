"""Accepts country and city names."""

from .field_validator import FieldValidator


class LocationValidator(FieldValidator):
    """Accepts country and city names, including multi-part destinations.
    The geonamescache name list is built once and then reused."""

    _known_names = None
    _lookup_failed = False

    def _check(self, value):
        if not value:
            return self._fail("Location cannot be empty.")
        if len(value) < 2:
            return self._fail("Location must contain at least 2 characters.")
        if len(value) > 100:
            return self._fail("Location must not exceed 100 characters.")

        names = self._names()
        if names is None:              # geonamescache unavailable: accept
            return self._ok(value)
        if " ".join(value.split()).lower() in names:
            return self._ok(value)
        return self._fail(
            "Location not found. Please enter a valid country or city name.")

    @classmethod
    def _names(cls):
        if cls._known_names is None and not cls._lookup_failed:
            try:
                from geonamescache import GeonamesCache
                geonames = GeonamesCache()
                names = set()
                for code, country in geonames.get_countries().items():
                    names.add(code.lower())
                    names.add(str(country.get("name", "")).lower())
                for city in geonames.get_cities().values():
                    names.add(str(city.get("name", "")).lower())
                cls._known_names = frozenset(names)
            except Exception:          # noqa: BLE001 - fall back to accepting
                cls._lookup_failed = True
        return cls._known_names
