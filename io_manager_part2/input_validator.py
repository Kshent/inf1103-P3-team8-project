"""Interface (abstract base class) for input validators."""

from abc import ABC, abstractmethod


class InputValidator(ABC):
    """Interface/abstract base class for input validators."""

    @abstractmethod
    def validate(self, value: str):
        """Return the validation result required by the concrete validator."""
