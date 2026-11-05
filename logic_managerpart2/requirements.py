"""requirements.py - What the user asked for, and how many points each category is worth."""
from .config import ScoringConfig
from .utils import DataUtils
from .preferences import PreferenceParser


class Requirements:
    """Works out, once per search, what will be scored and how many points
    each category is worth. Call to_dict() to hand it to the output layer."""

    def __init__(self, ai_output, record, parser=None):
        parser = parser or PreferenceParser()
        self._targets = self.extract_targets(ai_output)
        self._pref_checks, self._unverified = parser.parse(
            record.get("preferences"), self._targets)

        budget_min = record.get("budget_min")
        budget_max = record.get("budget_max")
        self._budget_min = budget_min if DataUtils.is_number(budget_min) else None
        self._budget_max = budget_max if DataUtils.is_number(budget_max) else None

        active = ["rating", "price"]
        self._not_scored = []
        if self._targets:
            active.append("location")
        else:
            self._not_scored.append(
                "Location was not scored: You did not ask to be near a place.")
        if self._pref_checks:
            active.append("preferences")
        else:
            self._not_scored.append(
                "Amenity preferences were not scored: Nothing you asked for "
                "could be checked against the hotel data.")
        if self._not_scored:
            self._not_scored.append(
                "Points for unscored categories are shared across the scored "
                "ones, so every score is still out of 100.")

        self._maxima = self._allocate_maxima(active)

    # read-only access
    @property
    def budget_min(self):
        return self._budget_min

    @property
    def budget_max(self):
        return self._budget_max

    @property
    def targets(self):
        return self._targets

    @property
    def pref_checks(self):
        return self._pref_checks

    @property
    def unverified(self):
        return self._unverified

    @property
    def maxima(self):
        return self._maxima

    @property
    def not_scored(self):
        return self._not_scored

    @staticmethod
    def extract_targets(ai_output):
        """Places the user asked to be near, as extracted by the AI."""
        targets = []
        if not isinstance(ai_output, dict):
            return targets
        proximity = ai_output.get("proximity_preference")
        if (not isinstance(proximity, dict)
                or proximity.get("specified") is not True):
            return targets
        for target in DataUtils.as_list(proximity.get("preferences")):
            if isinstance(target, str) and target.strip():
                targets.append(target.strip())
        return targets

    @staticmethod
    def _allocate_maxima(active):
        """Share BASE_POINTS across the scored categories using whole numbers
        that add up to exactly BASE_POINTS."""
        weights = ScoringConfig.WEIGHTS
        base = ScoringConfig.BASE_POINTS
        order = ScoringConfig.CATEGORY_ORDER
        total = sum(weights[key] for key in active)
        raw = {key: weights[key] * base / total for key in active}
        maxima = {key: int(round(raw[key], 9)) for key in active}
        leftover = base - sum(maxima.values())
        by_remainder = sorted(
            active,
            key=lambda key: (-(raw[key] - maxima[key]), order.index(key)))
        for key in by_remainder[:leftover]:
            maxima[key] += 1
        return maxima

    def to_dict(self):
        return {
            "budget_min": self._budget_min,
            "budget_max": self._budget_max,
            "targets": self._targets,
            "pref_checks": self._pref_checks,
            "unverified": self._unverified,
            "maxima": self._maxima,
            "not_scored": self._not_scored,
        }
