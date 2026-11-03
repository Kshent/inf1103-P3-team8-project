from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Interface (must-be-able-to-do): turn a prompt into response text.

    Liskov contract every implementation must honour:
      * return the raw response text, or None when no usable text exists;
      * never raise to the caller.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name, used in log messages."""

    @abstractmethod
    def call_api(self, prompt: str) -> str | None:
        """Return raw AI response text, or None."""
