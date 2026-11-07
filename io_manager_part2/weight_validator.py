"""Validates the points given to one scoring criterion."""

from .input_validator import InputValidator


class WeightValidator(InputValidator):
    """Accepts a whole number from 0 up to the points still left to assign."""

    def __init__(self, remaining: int = 100):
        self._remaining = remaining

    def validate(self, points: str) -> tuple[bool, str, int | None]:
        if not isinstance(points, str) or not (points.isascii() and points.isdigit()):
            return (
                False,
                f"Please enter a whole number from 0 to {self._remaining}.",
                None,
            )

        value = int(points)
        if value > self._remaining:
            return (
                False,
                "That would take your total above 100. "
                f"You only have {self._remaining} point(s) left to assign.",
                None,
            )
        return True, "", value
