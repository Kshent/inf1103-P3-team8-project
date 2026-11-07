"""hotel.py - Hotel: one hotel, the facts read from it, and what happened to it."""
import re


class Hotel:
    """One hotel from the AI's list.

    Holds the hotel's data, reads facts from it, and records what happens to it
    as it moves through the pipeline (flags, outcome, score, ...).
    It never talks to any other class: LogicManager passes in whatever it needs
    as plain data and takes the results back.
    """

    def __init__(self, raw):
        # Shallow copy: the AI's dict is never modified.
        self.record = dict(raw)
        self.name = raw.get("name")
        self.price = raw.get("price_per_night_sgd")
        self.rating = raw.get("rating")
        self.amenities = raw.get("amenities")
        self.distances = raw.get("distance_to_preferences")
        self.flags = []
        self.outcome = None
        self.reject_reason = None
        self.score = None
        self.score_max = None
        self.verdict = None
        self.breakdown = None

    # Static helpers
    @staticmethod
    def is_record(raw):
        """True if the AI item is a dict (anything else is skipped)."""
        return isinstance(raw, dict)

    @staticmethod
    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def as_list(value):
        return value if isinstance(value, list) else []

    @staticmethod
    def norm_name(name):
        """Normalise a hotel name for duplicate detection and stable sorting."""
        return " ".join(str(name).lower().split())

    @staticmethod
    def has_term(text, term):
        """Whole-word match, so 'spa' does not match 'spacious'."""
        return re.search(r"\b" + re.escape(term) + r"\b", text) is not None

    @staticmethod
    def has_any(text, terms):
        return any(Hotel.has_term(text, term) for term in terms)

    # Checks
    def is_usable(self):
        """A hotel needs a name and a usable price."""
        if not isinstance(self.name, str) or not self.name.strip():
            return False
        if not self.is_number(self.price) or self.price <= 0:
            return False
        return True

    def norm_key(self):
        """The name in a form that is safe to compare."""
        return self.norm_name(self.name)

    def compute_flags(self, targets):
        """Attach warnings for data that is missing or suspicious."""
        flags = []
        if not self.is_number(self.rating):
            flags.append("rating_missing")
        elif float(self.rating).is_integer():
            flags.append("rating_may_be_stars")
        if not self.as_list(self.amenities):
            flags.append("amenities_missing")
        if any(self.distance_for(target) is None for target in targets):
            flags.append("distance_unknown")
        self.flags = flags
        self.record["flags"] = flags
        return flags

    # Facts
    def distance_for(self, target):
        """Distance in metres from this hotel to a target, or None if unknown."""
        for item in self.as_list(self.distances):
            if not isinstance(item, dict):
                continue
            name = item.get("target")
            if isinstance(name, str) and name.strip().lower() == target.lower():
                distance = item.get("distance_m")
                if self.is_number(distance) and distance >= 0:
                    return distance
                return None
        return None

    def amenity_matches(self, pref_checks, amenity_terms):
        """Return (met, missing): requested amenities this hotel has / lacks."""
        amenities = [str(item) for item in self.as_list(self.amenities)]
        met = []
        missing = []
        for label in pref_checks:
            found = None
            for amenity in amenities:
                if self.has_any(amenity.lower(), amenity_terms[label]):
                    found = amenity
                    break
            if found:
                met.append("%s (%s)" % (label, found))
            else:
                missing.append(label)
        return met, missing

    def facts(self, targets, pref_checks, amenity_terms):
        """Everything the filter and scorer need to know about this hotel, as
        plain data. 'distances' lines up with 'targets', one entry each."""
        met, missing = self.amenity_matches(pref_checks, amenity_terms)
        return {
            "price": self.price,
            "rating": self.rating,
            "distances": [self.distance_for(target) for target in targets],
            "met": met,
            "missing": missing,
        }

    # Recording what happened
    def mark_rejected(self, reason):
        self.outcome = "rejected"
        self.reject_reason = reason
        self.record["outcome"] = "rejected"
        self.record["reject_reason"] = reason

    def mark_kept(self):
        self.outcome = "flagged" if self.flags else "accepted"
        self.record["outcome"] = self.outcome

    def apply_score(self, parts):
        """Store the score fields worked out by the scorer."""
        self.score = parts["score"]
        self.score_max = parts["score_max"]
        self.verdict = parts["verdict"]
        self.breakdown = parts["breakdown"]
        self.record["score"] = self.score
        self.record["score_max"] = self.score_max
        self.record["verdict"] = self.verdict
        self.record["breakdown"] = self.breakdown

    def to_dict(self):
        """The hotel as a plain dict: the AI's fields, then the fields added by
        each stage, in the order they were added."""
        return dict(self.record)
