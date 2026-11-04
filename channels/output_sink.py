"""Interface: anything the view can write lines to."""

from abc import ABC, abstractmethod


class OutputSink(ABC):
    @abstractmethod
    def write(self, text):
        """Show one line of text."""
