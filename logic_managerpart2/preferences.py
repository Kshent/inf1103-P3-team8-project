"""preferences.py - Turns the user's free text into checkable amenities."""
import re
from .config import ScoringConfig
from .utils import DataUtils


class PreferenceParser:
    """Splits the user's free text into amenity checks we can verify and
    phrases we cannot verify from hotel data (e.g. '3 beds', 'quiet room')."""

    @staticmethod
    def _split_phrases(text):
        parts = re.split(r",|;|&|\band\b|\bplus\b|\bwith\b", text or "",
                         flags=re.IGNORECASE)
        return [part.strip() for part in parts if part and part.strip()]

    @staticmethod
    def _mentions_target(phrase, targets):
        """True if the phrase is about one of the places the AI extracted."""
        words = set(re.findall(r"[a-z0-9]+", phrase.lower()))
        for target in targets:
            key = (set(re.findall(r"[a-z0-9]+", target.lower()))
                   - ScoringConfig.GENERIC_PLACE_WORDS)
            if key and key & words:
                return True
        return False

    def parse(self, text, targets):
        """Return (checks, unverified)."""
        checks = []
        unverified = []
        for phrase in self._split_phrases(text):
            lowered = phrase.lower()
            label = None
            for group_label, triggers, _terms in ScoringConfig.PREFERENCE_GROUPS:
                if DataUtils.has_any(lowered, triggers):
                    label = group_label
                    break
            if label:
                if label not in checks:
                    checks.append(label)
            elif (targets
                  and DataUtils.has_any(lowered, ScoringConfig.PROXIMITY_WORDS)
                  and self._mentions_target(lowered, targets)):
                continue          # handled by the Location category
            else:
                unverified.append(phrase)
        return checks, unverified
