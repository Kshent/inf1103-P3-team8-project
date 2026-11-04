"""Accepts price ranges such as 100-250 or SGD 100-SGD 250."""

import re

from .field_validator import FieldValidator


class PriceRangeValidator(FieldValidator):
    """Accepts 100-250, 100,250, 100to250, SGD 100-SGD 250 ..."""

    _PATTERN = re.compile(r"(\d+(?:\.\d+)?)(?:-|,|TO)(\d+(?:\.\d+)?)")

    def _check(self, value):
        if not value:
            return self._fail("Price range cannot be empty.")

        cleaned = value.upper().replace("SGD", "").replace("S$", "")
        cleaned = re.sub(r"\s+", "", cleaned.replace("$", ""))
        match = self._PATTERN.fullmatch(cleaned)
        if not match:
            return self._fail("Enter a valid SGD price range, for example "
                              "100-250 or SGD 100-SGD 250.")

        minimum = float(match.group(1))
        maximum = float(match.group(2))
        if minimum <= 0 or maximum <= 0:
            return self._fail("Prices must be greater than zero.")
        if minimum > maximum:
            return self._fail("The minimum price cannot be higher than the "
                              "maximum price.")
        if maximum > 1_000_000:
            return self._fail("The maximum price is too high.")

        return self._ok({"min": round(minimum, 2), "max": round(maximum, 2),
                         "currency": "SGD"})
