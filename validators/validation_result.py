"""The outcome of validating one answer."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str = ""
    value: Any = None
