from __future__ import annotations

from abc import ABC, abstractmethod


class ResponseValidator(ABC):
    """Abstract class: subclasses define the schema, this class shares the API.

    find_errors() is the one abstract operation. validate_response() is shared
    behaviour implemented once here, so every domain validator gets it free.
    """

    @abstractmethod
    def find_errors(self, data) -> list[str]:
        """Return human-readable problems. An empty list means valid."""

    def validate_response(self, data) -> bool:
        return not self.find_errors(data)
