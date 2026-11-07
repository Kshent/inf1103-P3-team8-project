"""
I/O Manager - object-oriented version.

Responsibilities remain limited to CLI input, validation and presentation.
Hotel ranking, AI recommendation and persistence stay in their own managers.

Package layout (one class per file):
    input_validator.py        InputValidator (abstract base class)
    location_validator.py     LocationValidator
    price_range_validator.py  PriceRangeValidator
    email_validator.py        EmailValidator
    input_reader.py           InputReader
    console_view.py           ConsoleView (what app.py uses)
"""