"""Accepts one of a fixed set of answers (menus)."""

from .field_validator import FieldValidator


class ChoiceValidator(FieldValidator):
    def __init__(self, choices, message):
        self.__choices = tuple(choices)
        self.__message = message

    def _check(self, value):
        if value in self.__choices:
            return self._ok(value)
        return self._fail(self.__message)