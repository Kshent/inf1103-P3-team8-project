"""scoring_config.py - the rulebook: every number and wording table in one place.

Scoring (always out of 100):
  Base points = 90, shared between these categories:
    Customer review rating  25   how well guests rated the hotel
    Price                   20   fit against the user's budget
    Location                25   distance to the places the user asked to be near
    Your preferences        20   requested amenities found in the hotel's amenities
  Top-match bonus = 10, awarded only when ALL conditions hold at the same time.
"""


class ScoringConfig:
    """Holds every threshold, weight and wording table used by the logic layer
    and hands each class only the slice of settings it needs.

    No other class reads this one directly: LogicManager asks for a slice and
    passes it to the right class as plain data."""

    def __init__(self):
        # Points
        self.base_points = 90
        self.bonus_points = 10
        self.weights = {"rating": 25, "price": 20, "location": 25,
                        "preferences": 20}
        self.category_order = ["rating", "price", "location", "preferences"]
        self.labels = {
            "rating": "Customer review rating",
            "price": "Price",
            "location": "Location",
            "preferences": "Your preferences",
            "bonus": "Top-match bonus",
        }

        # Hard filters
        self.min_acceptable_rating = 3.5   # review rating below this is rejected
        self.max_near_distance_m = 2000    # farther than this from a place is rejected

        # Bonus thresholds
        self.bonus_min_rating = 4.5
        self.bonus_max_distance_m = 300

        self.top_n = 3

        # Rating 3.0 earns nothing, 5.0 earns everything, linear in between
        self.rating_floor = 3.0
        self.rating_ceiling = 5.0
        self.rating_bands = [(4.5, "excellent"), (4.0, "very good"),
                             (3.5, "good")]
        self.rating_below = "below average"

        # (max distance in metres, share of location points, label)
        self.distance_bands = [
            (200, 1.00, "very close"),
            (500, 0.80, "short walk"),
            (1000, 0.60, "walkable"),
            (2000, 0.35, "a bit far"),
            (5000, 0.15, "far"),
        ]
        self.distance_beyond = (0.0, "very far")

        # Price: up to this share of the maximum budget earns full points
        self.price_full_points_ratio = 0.7
        self.price_min_share_at_max = 0.5  # a hotel exactly at the maximum earns half

        self.verdicts = [(85, "Excellent match"), (70, "Good match"),
                         (55, "Fair match")]
        self.verdict_low = "Weak match"

        # Words that mean "near a place" (handled by Location, not by amenities)
        self.proximity_words = ["near", "close to", "next to",
                                "walking distance", "nearby", "around"]

        # (label shown to the user, words in the user's text,
        #  words in hotel amenities)
        self.preference_groups = [
            ("swimming pool", ["pool", "pools", "swim", "swimming"],
             ["pool", "pools"]),
            ("gym", ["gym", "fitness", "workout"], ["gym", "fitness"]),
            ("spa", ["spa", "wellness", "massage"], ["spa", "wellness"]),
            ("free Wi-Fi", ["wifi", "wi-fi", "internet"], ["wifi", "wi-fi"]),
            ("breakfast", ["breakfast"], ["breakfast"]),
            ("family-friendly",
             ["family", "kid", "kids", "child", "children"],
             ["family", "kids", "child", "children", "babysitting"]),
            ("bathtub", ["bathtub", "bath tub"], ["bathtub", "bath tub"]),
            ("kitchen", ["kitchen", "kitchenette"], ["kitchen", "kitchenette"]),
            ("parking", ["parking", "car park"], ["parking", "car park"]),
            ("halal food", ["halal"], ["halal"]),
            ("high floor",
             ["high floor", "high floors", "high-floor", "upper floor"],
             ["high floor", "high floors", "high-floor", "upper floor"]),
            ("metro access",
             ["metro", "mrt", "subway", "public transport", "train"],
             ["metro", "mrt", "subway", "train", "public transport"]),
        ]

        # Words that say nothing about WHICH place (ignored when matching a
        # phrase like "near nanjing street" to the place the AI extracted)
        self.generic_place_words = {"road", "street", "st", "rd", "avenue",
                                    "ave", "the", "of", "and", "near",
                                    "singapore"}

        self.flag_messages = {
            "rating_missing": "No customer review rating was available.",
            "rating_may_be_stars": (
                "The rating is a whole number, so it may be a hotel's number "
                "of stars rather than an average of guest reviews. Please "
                "verify."),
            "amenities_missing": "No amenities were listed.",
            "distance_unknown": "Distance to a requested place is unknown.",
        }

    # The slices each class needs
    def requirements_settings(self):
        """Settings for Requirements (reading the user's wishes)."""
        return {
            "base_points": self.base_points,
            "weights": self.weights,
            "category_order": self.category_order,
            "proximity_words": self.proximity_words,
            "preference_groups": self.preference_groups,
            "generic_place_words": self.generic_place_words,
        }

    def hotel_settings(self):
        """Settings for Hotel: the hotel-amenity words for each requested
        amenity label."""
        return {
            "amenity_terms": {label: terms for label, _triggers, terms
                              in self.preference_groups},
        }

    def filter_settings(self):
        """Settings for HotelFilter (the mandatory rules)."""
        return {
            "min_acceptable_rating": self.min_acceptable_rating,
            "max_near_distance_m": self.max_near_distance_m,
        }

    def scorer_settings(self):
        """Settings for HotelScorer (points, bands, labels, verdicts)."""
        return {
            "base_points": self.base_points,
            "bonus_points": self.bonus_points,
            "labels": self.labels,
            "bonus_min_rating": self.bonus_min_rating,
            "bonus_max_distance_m": self.bonus_max_distance_m,
            "top_n": self.top_n,
            "rating_floor": self.rating_floor,
            "rating_ceiling": self.rating_ceiling,
            "rating_bands": self.rating_bands,
            "rating_below": self.rating_below,
            "distance_bands": self.distance_bands,
            "distance_beyond": self.distance_beyond,
            "price_full_points_ratio": self.price_full_points_ratio,
            "price_min_share_at_max": self.price_min_share_at_max,
            "verdicts": self.verdicts,
            "verdict_low": self.verdict_low,
        }
