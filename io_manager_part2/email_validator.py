"""Validates a traveller email address."""

import re

from .input_validator import InputValidator


class EmailValidator(InputValidator):
    """Validates a traveller email address."""

    def validate(self, email_address: str) -> tuple[bool, str]:
        if not isinstance(email_address, str) or not email_address:
            return False, "Email address cannot be empty."
        if len(email_address) > 254:
            return False, "Email address is too long."

        pattern = (
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
            r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
        )
        if not re.fullmatch(pattern, email_address):
            return False, "Please enter a valid email address."
        return True, ""
