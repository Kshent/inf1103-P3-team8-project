"""Interface: anything the view can read answers from."""

from abc import ABC, abstractmethod


class InputSource(ABC):
    @abstractmethod
    def read(self, prompt):
        """Show the prompt and return the user's reply, stripped."""
