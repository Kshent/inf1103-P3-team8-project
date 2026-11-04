"""io_manager - Layer 1: everything the traveller sees and types.

Responsibilities:
  1. Collect traveller input from the CLI.
  2. Validate user-provided information.
  3. Display hotel recommendations and saved records.

This layer must not contain hotel ranking logic, AI logic or file storage.
It also does not import the other layers: it receives plain dictionaries
(and, for admin login and profile choices, small objects/lists passed in by
app.py) and returns plain dictionaries.

Package layout (one class per file)
-----------------------------------
  io_manager/
    console_view.py        ConsoleView       asks questions, shows results
    hotel_formatter.py     HotelFormatter    builds text lines, never prints
    exceptions.py          InputCancelled
    channels/              InputSource, ConsoleInput, ScriptedInput,
                           OutputSink, ConsoleOutput, BufferOutput
    validators/            FieldValidator (abstract), ValidationResult and the
                           Location / PriceRange / Email / Preferences /
                           Choice / Weight validators

Dependencies point one way only: console_view -> channels, validators,
hotel_formatter. Nothing in those imports console_view.

Everything public is re-exported here, so other code can simply write
`import io_manager as IOManager` and use IOManager.ConsoleView()."""

from .exceptions import InputCancelled
from .channels import (InputSource, ConsoleInput, ScriptedInput,
                       OutputSink, ConsoleOutput, BufferOutput)
from .validators import (ValidationResult, FieldValidator, LocationValidator,
                         PriceRangeValidator, EmailValidator,
                         PreferencesValidator, ChoiceValidator,
                         WeightValidator)
from .hotel_formatter import HotelFormatter
from .console_view import ConsoleView

__all__ = ["InputCancelled",
           "InputSource",
           "ConsoleInput",
           "ScriptedInput",
           "OutputSink",
           "ConsoleOutput",
           "BufferOutput",
           "ValidationResult",
           "FieldValidator",
           "LocationValidator",
           "PriceRangeValidator",
           "EmailValidator",
           "PreferencesValidator",
           "ChoiceValidator",
           "WeightValidator",
           "HotelFormatter",
           "ConsoleView"]
