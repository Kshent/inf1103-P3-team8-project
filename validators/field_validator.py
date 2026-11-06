"""Abstract base for all field validators (template method)."""

from abc import ABC, abstractmethod

from .validation_result import ValidationResult


class FieldValidator(ABC):
    """validate() is the template: normalise the text, then run the
    subclass's own _check()."""

    def validate(self, raw):
        if not isinstance(raw, str):
            return self._fail("Value must be text.")
        return self._check(self._normalise(raw))

    def _normalise(self, raw):
        return raw.strip()

    @abstractmethod
    def _check(self, value):
        ...

    @staticmethod
    def _ok(value):
        return ValidationResult(True, "", value)

    @staticmethod
    def _fail(message):
        return ValidationResult(False, message, None)