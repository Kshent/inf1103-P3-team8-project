"""Reads answers from the keyboard."""

from ..exceptions import InputCancelled
from .input_source import InputSource


class ConsoleInput(InputSource):
    """Reads from the keyboard. Turns Ctrl-C / Ctrl-D into InputCancelled so
    the application never crashes with a traceback."""

    def __init__(self, input_function=input):
        self.__input = input_function

    def read(self, prompt):
        try:
            value = self.__input(prompt)
        except (KeyboardInterrupt, EOFError):
            raise InputCancelled("\nInput cancelled. Goodbye.") from None
        if value is None:
            raise InputCancelled("\nInput cancelled. Goodbye.")
        return value.strip()
