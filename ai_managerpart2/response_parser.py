from __future__ import annotations

from abc import ABC, abstractmethod


class ResponseParser(ABC):
    """Interface: turn raw model text into a dictionary (or None)."""

    @abstractmethod
    def parse_response(self, raw_text: str | None) -> dict | None:
        """Return the parsed object, or None if it cannot be parsed."""
