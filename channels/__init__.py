"""Where input comes from and where output goes (interfaces and implementations)."""

from .input_source import InputSource
from .console_input import ConsoleInput
from scripted_input import ScriptedInput
from .output_sink import OutputSink
from .console_output import ConsoleOutput
from .buffer_output import BufferOutput

__all__ = [
    "InputSource",
    "ConsoleInput",
    "ScriptedInput",
    "OutputSink",
    "ConsoleOutput",
    "BufferOutput",
]
