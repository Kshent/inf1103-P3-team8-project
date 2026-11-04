"""Returns pre-written answers (for tests and demos)."""

from ..exceptions import InputCancelled
from .input_source import InputSource


class ScriptedInput(InputSource):
    """Returns pre-written answers one by one (for tests and demos)."""

    def __init__(self, answers):
        self.__answers = list(answers)
        self.prompts = []             # every prompt that was shown

    def read(self, prompt):
        self.prompts.append(prompt)
        if not self.__answers:
            raise InputCancelled("\nInput cancelled. Goodbye.")
        return str(self.__answers.pop(0)).strip()
