"""Collects output in a list instead of showing it (for tests)."""

from .output_sink import OutputSink


class BufferOutput(OutputSink):
    """Collects output in a list instead of showing it (for tests)."""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)
