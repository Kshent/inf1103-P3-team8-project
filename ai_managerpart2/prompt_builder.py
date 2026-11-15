from __future__ import annotations

from abc import ABC, abstractmethod


class PromptBuilder(ABC):
    """Interface: build the normal prompt and the one correction prompt."""

    @abstractmethod
    def build_prompt(self, record: dict) -> str:
        """Build the first prompt for a user record."""

    @abstractmethod
    def build_correction_prompt(
        self,
        original_prompt: str,
        invalid_response: str,
    ) -> str:
        """Build the correction prompt after invalid AI output."""
