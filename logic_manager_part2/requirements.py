"""requirements.py - Requirements: what the user asked for, and how many points
each scored category is worth."""
import re


class Requirements:
    """Works out, once per search, what will be scored and how many points each
    category is worth. Call to_dict() to hand the result to the output layer.

    It never talks to any other class: LogicManager gives it the settings it
    needs as plain data."""

    def __init__(self, ai_output, record, settings):
        
        self._base_points = settings["base_points"]
        self._weights = settings["weights"].copy()
        self._category_order = settings["category_order"]
        self._redistribute_unscored = settings.get(
            "redistribute_unscored", True
        )
        self._proximity_words = settings["proximity_words"]
        self._preference_groups = settings["preference_groups"]
        self._generic_place_words = settings["generic_place_words"]

        self._targets = self.extract_targets(ai_output)
        self._pref_checks, self._unverified = self.parse_preferences(
            record.get("preferences"))

        budget_min = record.get("budget_min")
        budget_max = record.get("budget_max")
        self._budget_min = budget_min if self.is_number(budget_min) else None
        self._budget_max = budget_max if self.is_number(budget_max) else None

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

            if self._redistribute_unscored:
                self._not_scored.append(
                    "Points for unscored categories are shared "
                    "across the applicable categories."
                )

            else:
                self._not_scored.append(
                    "Custom weightages are not redistributed. "
                    "Unavailable categories receive 0 points."
                )


        self._maxima = self.allocate_maxima(active)

    # Read-only access
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

    # Small helpers (this class keeps its own copies on purpose, so it does
    # not depend on any other class)
    @staticmethod
    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def as_list(value):
        return value if isinstance(value, list) else []

    @staticmethod
    def has_term(text, term):
        """Whole-word match, so 'spa' does not match 'spacious'."""
        return re.search(r"\b" + re.escape(term) + r"\b", text) is not None

    @staticmethod
    def has_any(text, terms):
        return any(Requirements.has_term(text, term) for term in terms)
    
    
    @classmethod
    def available_weight_keys(cls, preferences, settings):

        # These three categories are always available
        allowed = {"rating", "price", "bonus"}

        if not isinstance(preferences, str) or not preferences.strip():
            return allowed

        text = preferences.lower()

        # Location: user wants to be near somewhere
        if cls.has_any(text, settings["proximity_words"]):
            allowed.add("location")

        # Preferences: user mentions an amenity we can check
        for label, triggers, terms in settings["preference_groups"]:
            if cls.has_any(text, triggers):
                allowed.add("preferences")
                break

        return allowed
        

    # Reading the user's wishes
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
        for target in Requirements.as_list(proximity.get("preferences")):
            if isinstance(target, str) and target.strip():
                targets.append(target.strip())
        return targets

    @staticmethod
    def split_phrases(text):
        """Cut the user's text into separate wishes."""
        parts = re.split(r",|;|&|\band\b|\bplus\b|\bwith\b", text or "",
                         flags=re.IGNORECASE)
        return [part.strip() for part in parts if part and part.strip()]

    def mentions_target(self, phrase):
        """True if the phrase is about one of the places the AI extracted."""
        words = set(re.findall(r"[a-z0-9]+", phrase.lower()))
        for target in self._targets:
            key = (set(re.findall(r"[a-z0-9]+", target.lower()))
                   - self._generic_place_words)
            if key and key & words:
                return True
        return False

    def parse_preferences(self, text):
        """Split the user's free text into amenity checks we can verify and
        phrases we cannot verify from hotel data (e.g. '3 beds', 'quiet
        room'). Returns (checks, unverified)."""
        checks = []
        unverified = []
        for phrase in self.split_phrases(text):
            lowered = phrase.lower()
            label = None
            for group_label, triggers, _terms in self._preference_groups:
                if self.has_any(lowered, triggers):
                    label = group_label
                    break
            if label:
                if label not in checks:
                    checks.append(label)
            elif (self._targets
                  and self.has_any(lowered, self._proximity_words)
                  and self.mentions_target(lowered)):
                continue          # handled by the Location category
            else:
                unverified.append(phrase)
        return checks, unverified

    
    def allocate_maxima(self, active):
        # Option 4: Do not redistribute user-selected maximums
        if not self._redistribute_unscored:
            return {
                key: self._weights[key]
                for key in active
            }
        # Options 1-3: Redistribute unavailable base points
        total = sum(self._weights[key] for key in active)
        if total == 0:
            return {key: 0 for key in active}
        raw = {
            key: self._weights[key] * self._base_points / total
            for key in active
        }
        maxima = {
            key: int(round(raw[key], 9))
            for key in active
        }
        leftover = self._base_points - sum(maxima.values())
        by_remainder = sorted(
            active,
            key=lambda key: (
                -(raw[key] - maxima[key]),
                self._category_order.index(key)
            )
        )
        for key in by_remainder[:leftover]:
            maxima[key] += 1
        return maxima


    def to_dict(self):
        """Plain data for the output layer."""
        return {
            "budget_min": self._budget_min,
            "budget_max": self._budget_max,
            "targets": self._targets,
            "pref_checks": self._pref_checks,
            "unverified": self._unverified,
            "maxima": self._maxima,
            "not_scored": self._not_scored,
        }
