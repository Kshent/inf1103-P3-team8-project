"""Validates and normalises an SGD price range."""

import re

from .input_validator import InputValidator


class PriceRangeValidator(InputValidator):
    """Validates and normalises an SGD price range."""

    def validate(
        self, price_range: str
    ) -> tuple[bool, str, dict[str, int | float | str] | None]:
        if not isinstance(price_range, str) or not price_range.strip():
            return False, "Price range cannot be empty.", None

        cleaned = price_range.upper()
        for currency_marker in ("SGD", "S$", "$"):
            cleaned = cleaned.replace(currency_marker, "")
        cleaned = re.sub(r"\s+", "", cleaned)

        match = re.fullmatch(
            r"(\d+(?:\.\d+)?)(?:-|,|TO)(\d+(?:\.\d+)?)", cleaned
        )
        if not match:
            return (
                False,
                "Enter a valid SGD price range, for example 100-250 or SGD 100-SGD 250.",
                None,
            )

        minimum = float(match.group(1))
        maximum = float(match.group(2))
        if minimum <= 0 or maximum <= 0:
            return False, "Prices must be greater than zero.", None
        if minimum > maximum:
            return False, "The minimum price cannot be higher than the maximum price.", None
        if maximum > 1_000_000:
            return False, "The maximum price is too high.", None

        return True, "", {
            "min": round(minimum, 2),
            "max": round(maximum, 2),
            "currency": "SGD",
        }
