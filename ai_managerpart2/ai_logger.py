from abc import ABC, abstractmethod


class AILogger(ABC):
    """Interface: anything that can record AI Manager warnings and errors.

    AIManager and the providers depend on this abstraction (DIP), so tests can
    inject an in-memory logger and production can write to a file.
    """

    @abstractmethod
    def warning(self, message: str, *args) -> None:
        """Record a recoverable problem."""

    @abstractmethod
    def error(self, message: str, *args) -> None:
        """Record a failure."""
