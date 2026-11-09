"""Reads and normalizes user input from the command line."""


class InputReader:
    """Wraps an input function and handles user cancellation consistently."""

    def __init__(self, input_function=input):
        self._input = input_function

    def read(self, prompt: str) -> str:
        """Return trimmed input, or raise EOFError when input is cancelled."""
        try:
            value = self._input(prompt)
        except (KeyboardInterrupt, EOFError):
            raise EOFError("\nInput cancelled. Goodbye.") from None
        if value is None:
            raise EOFError("\nInput cancelled. Goodbye.")
        return value.strip()
