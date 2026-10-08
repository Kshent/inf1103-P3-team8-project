import os
import json
import re


def _strip_code_fences(text):
    """Remove ```json ... ``` or plain ``` ... ``` wrappers."""
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _extract_json_block(text):
    """Pull out the first {...} block in case the model added stray
    commentary before or after the JSON."""
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text