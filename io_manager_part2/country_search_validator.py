"""Validates the country text used to search saved hotel records."""

import re

from .input_validator import InputValidator


class CountrySearchValidator(InputValidator):
    """Validates a full or partial country name used to search records.

    Unlike LocationValidator, the text does not have to be a whole country
    name, so "singa" is accepted (it finds Singapore).
    """

    MIN_LENGTH = 2
    MAX_LENGTH = 60

    def validate(self, country: str) -> tuple[bool, str]:
        if not isinstance(country, str) or not country.strip():
            return False, "Country cannot be empty."

        country = " ".join(country.split())
        if len(country) < self.MIN_LENGTH:
            return False, (
                f"Country must contain at least {self.MIN_LENGTH} characters."
            )
        if len(country) > self.MAX_LENGTH:
            return False, (
                f"Country must not exceed {self.MAX_LENGTH} characters."
            )
        if not re.fullmatch(r"[^\W\d_]+(?:[ .,'’()-]+[^\W\d_]*)*", country):
            return False, (
                "Country can only contain letters, spaces and . , ' ( ) -"
            )
        return True, ""