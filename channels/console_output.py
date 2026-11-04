"""Writes to the screen."""

from .output_sink import OutputSink


class ConsoleOutput(OutputSink):
    def __init__(self, output_function=print):
        self.__output = output_function

    def write(self, text):
        self.__output(text)
