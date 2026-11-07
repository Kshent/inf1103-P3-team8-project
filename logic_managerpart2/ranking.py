"""ranking.py - Ranks scored hotels and picks the top ones."""
from .config import ScoringConfig
from .utils import DataUtils


class HotelRanker:
    """Ranks scored hotels and picks the best ones."""

    def rank(self, hotels):
        """Sort by score (high to low). Ties go to the higher customer rating,
        then the lower price, then the name, so the same input always gives
        the same order."""
        def sort_key(hotel):
            rating = hotel.get("rating")
            return (-hotel["score"],
                    -(rating if DataUtils.is_number(rating) else 0),
                    hotel["price_per_night_sgd"],
                    DataUtils.norm_name(hotel["name"]))
        return sorted(hotels, key=sort_key)

    def top(self, ranked_hotels):
        """Return up to TOP_N distinct hotels from an already-ranked list.
        Returns fewer if fewer exist; never pads or crashes."""
        top = []
        seen = set()
        for hotel in ranked_hotels:
            key = DataUtils.norm_name(hotel["name"])
            if key in seen:
                continue
            seen.add(key)
            entry = dict(hotel)
            entry["rank"] = len(top) + 1
            top.append(entry)
            if len(top) == ScoringConfig.TOP_N:
                break
        return top
