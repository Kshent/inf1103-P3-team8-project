"""Points for one scoring criterion, limited to the points left."""

from .field_validator import FieldValidator


class WeightValidator(FieldValidator):
    """Points for one scoring criterion: a whole number from 0 up to the
    points still left to assign (so the total can never go above 100)."""

    def __init__(self, remaining):
        self.__remaining = remaining

    def _check(self, value):
        if not (value.isascii() and value.isdigit()):
            return self._fail("Please enter a whole number from 0 to %d."
                              % self.__remaining)
        points = int(value)
        if points > self.__remaining:
            return self._fail(
                "That would take your total above 100. You only have %d "
                "point(s) left to assign." % self.__remaining)
        return self._ok(points)