"""validation.py - Drops unusable hotels and attaches data-quality flags."""
from .utils import DataUtils
from .facts import HotelFacts
from .requirements import Requirements


class HotelValidator:
    """Returns the usable hotels from the ai_manager result.

    ai_manager checks the structure. This checks usefulness: drops records
    without a name or a usable price, removes duplicate names, and attaches a
    'flags' list for data that is missing or suspicious. Never raises.
    """

    def validate(self, ai_output):
        if not isinstance(ai_output, dict):
            return []
        hotels = ai_output.get("hotels")
        if not isinstance(hotels, list):
            return []

        targets = Requirements.extract_targets(ai_output)
        valid = []
        seen = set()
        for hotel in hotels:
            if not isinstance(hotel, dict):
                continue
            name = hotel.get("name")
            price = hotel.get("price_per_night_sgd")
            if not isinstance(name, str) or not name.strip():
                continue
            if not DataUtils.is_number(price) or price <= 0:
                continue

            key = DataUtils.norm_name(name)
            if key in seen:
                continue
            seen.add(key)

            checked = dict(hotel)
            checked["flags"] = self._flags_for(hotel, targets)
            valid.append(checked)
        return valid

    @staticmethod
    def _flags_for(hotel, targets):
        flags = []
        rating = hotel.get("rating")
        if not DataUtils.is_number(rating):
            flags.append("rating_missing")
        elif float(rating).is_integer():
            flags.append("rating_may_be_stars")
        if not DataUtils.as_list(hotel.get("amenities")):
            flags.append("amenities_missing")
        if any(HotelFacts.distance_for(hotel, target) is None
               for target in targets):
            flags.append("distance_unknown")
        return flags
