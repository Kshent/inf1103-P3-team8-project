from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIAttempt:
    """Stores the result of one AI request attempt."""

    raw_text: str | None
    data: dict | None