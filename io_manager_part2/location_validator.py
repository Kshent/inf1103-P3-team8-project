"""Validates a country or city name."""

import re

from geonamescache import GeonamesCache

from .input_validator import InputValidator


class LocationValidator(InputValidator):
    """Validates a country or city name."""

    def __init__(self):
        self._geonames = GeonamesCache()

    def validate(self, location: str) -> tuple[bool, str]:
        if not isinstance(location, str):
            return False, "Location must be text."

        location = location.strip()
        if not location:
            return False, "Location cannot be empty."
        if len(location) < 2:
            return False, "Location must contain at least 2 characters."
        if len(location) > 100:
            return False, "Location must not exceed 100 characters."
        if not re.fullmatch(r"[^\W\d_][\w\s.,'’()-]*", location, re.UNICODE):
            return False, (
                "Location contains invalid characters. "
                "Please enter a valid country or city name."
            )

        try:
            normalized = " ".join(location.split()).lower()
            countries = self._geonames.get_countries()
            for country_code, country_data in countries.items():
                country_name = str(country_data.get("name", "")).lower()
                if normalized in (country_name, country_code.lower()):
                    return True, ""

            cities = self._geonames.get_cities()
            for city_data in cities.values():
                if normalized == str(city_data.get("name", "")).lower():
                    return True, ""

            return False, (
                "Location not found. Please enter a valid country or city name."
            )
        except Exception:
            # Preserve the original fallback if geonamescache is unavailable.
            return True, ""
