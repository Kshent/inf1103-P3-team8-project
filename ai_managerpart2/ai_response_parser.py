from __future__ import annotations

import json
import re

from .response_parser import ResponseParser


class AIResponseParser(ResponseParser):
    """Cleans raw model text and parses the first JSON object into a dict."""

    def parse_response(self, raw_ai_response_text: str | None) -> dict | None:
        """Return a dictionary on success, otherwise None."""
        if not isinstance(raw_ai_response_text, str):
            return None

        text = raw_ai_response_text.strip()
        if not text:
            return None

        text = self._extract_json_block(self._strip_code_fences(text))
        if not text:
            return None

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

        return data if isinstance(data, dict) else None

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove ```json ... ``` or plain ``` ... ``` wrappers."""
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return text

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Pull out the first {...} block if commentary surrounds the JSON."""
        if text.startswith("{") and text.endswith("}"):
            return text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text
