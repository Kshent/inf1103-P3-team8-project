"""Checks an email address."""

import re

from .field_validator import FieldValidator


class EmailValidator(FieldValidator):
    _PATTERN = re.compile(
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")

    def _check(self, value):
        if not value:
            return self._fail("Email address cannot be empty.")
        if len(value) > 254:          # RFC limit
            return self._fail("Email address is too long.")
        if not self._PATTERN.fullmatch(value):
            return self._fail("Please enter a valid email address.")
        return self._ok(value)
