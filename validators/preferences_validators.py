"""Optional free-text preferences."""

from .field_validator import FieldValidator


class PreferencesValidator(FieldValidator):
    """Preferences are optional: an empty answer is allowed."""

    MAX_LENGTH = 2_000

    def _check(self, value):
        if len(value) > self.MAX_LENGTH:
            return self._fail("Preferences must not exceed 2,000 characters.")
        return self._ok(value)