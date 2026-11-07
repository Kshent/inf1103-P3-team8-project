"""facts.py - Reads facts about a single hotel (distance, amenities)."""
from .config import ScoringConfig
from .utils import DataUtils


class HotelFacts:
    """Reads facts about a single hotel dict."""

    @staticmethod
    def distance_for(hotel, target):
        """Distance in metres from this hotel to a target, or None if unknown."""
        for item in DataUtils.as_list(hotel.get("distance_to_preferences")):
            if not isinstance(item, dict):
                continue
            name = item.get("target")
            if isinstance(name, str) and name.strip().lower() == target.lower():
                distance = item.get("distance_m")
                if DataUtils.is_number(distance) and distance >= 0:
                    return distance
                return None
        return None

    @staticmethod
    def amenity_matches(hotel, requirements):
        """Return (met, missing): requested amenities this hotel has / lacks."""
        amenities = [str(item)
                     for item in DataUtils.as_list(hotel.get("amenities"))]
        terms_by_label = {label: terms for label, _t, terms
                          in ScoringConfig.PREFERENCE_GROUPS}
        met = []
        missing = []
        for label in requirements.pref_checks:
            found = None
            for amenity in amenities:
                if DataUtils.has_any(amenity.lower(), terms_by_label[label]):
                    found = amenity
                    break
            if found:
                met.append("%s (%s)" % (label, found))
            else:
                missing.append(label)
        return met, missing
