"""config.py - Business-rule constants (weights, thresholds, wording tables)."""


class ScoringConfig:
    """Holds every threshold, weight and wording table in one place."""

    BASE_POINTS = 90
    BONUS_POINTS = 10
    WEIGHTS = {"rating": 25, "price": 20, "location": 25, "preferences": 20}
    CATEGORY_ORDER = ["rating", "price", "location", "preferences"]
    LABELS = {
        "rating": "Customer review rating",
        "price": "Price",
        "location": "Location",
        "preferences": "Your preferences",
        "bonus": "Top-match bonus",
    }

    # Hard filters
    MIN_ACCEPTABLE_RATING = 3.5      # customer review rating below this is rejected
    MAX_NEAR_DISTANCE_M = 2000       # farther than this from a requested place is rejected

    # Bonus thresholds
    BONUS_MIN_RATING = 4.5
    BONUS_MAX_DISTANCE_M = 300

    TOP_N = 3

    # Rating 3.0 earns nothing, 5.0 earns everything, linear in between
    RATING_FLOOR = 3.0
    RATING_CEILING = 5.0
    RATING_BANDS = [(4.5, "excellent"), (4.0, "very good"), (3.5, "good")]
    RATING_BELOW = "below average"

    # (max distance in metres, share of location points, label)
    DISTANCE_BANDS = [
        (200, 1.00, "very close"),
        (500, 0.80, "short walk"),
        (1000, 0.60, "walkable"),
        (2000, 0.35, "a bit far"),
        (5000, 0.15, "far"),
    ]
    DISTANCE_BEYOND = (0.0, "very far")

    # Price: up to this share of the maximum budget earns full points
    PRICE_FULL_POINTS_RATIO = 0.7
    PRICE_MIN_SHARE_AT_MAX = 0.5     # a hotel exactly at the maximum still earns half

    VERDICTS = [(85, "Excellent match"), (70, "Good match"), (55, "Fair match")]
    VERDICT_LOW = "Weak match"

    # Words that mean "near a place" (handled by Location, not by amenities)
    PROXIMITY_WORDS = ["near", "close to", "next to", "walking distance",
                       "nearby", "around"]

    # (label shown to the user, words in the user's text, words in hotel amenities)
    PREFERENCE_GROUPS = [
        ("swimming pool", ["pool", "pools", "swim", "swimming"],
         ["pool", "pools"]),
        ("gym", ["gym", "fitness", "workout"], ["gym", "fitness"]),
        ("spa", ["spa", "wellness", "massage"], ["spa", "wellness"]),
        ("free Wi-Fi", ["wifi", "wi-fi", "internet"], ["wifi", "wi-fi"]),
        ("breakfast", ["breakfast"], ["breakfast"]),
        ("family-friendly", ["family", "kid", "kids", "child", "children"],
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

    # Words that say nothing about WHICH place (ignored when matching a phrase
    # like "near nanjing street" to the place the AI extracted)
    GENERIC_PLACE_WORDS = {"road", "street", "st", "rd", "avenue", "ave",
                           "the", "of", "and", "near", "singapore"}

    FLAG_MESSAGES = {
        "rating_missing": "No customer review rating was available.",
        "rating_may_be_stars": (
            "The rating is a whole number, so it may be a hotel's number of "
            "stars rather than an average of guest reviews. Please verify."),
        "amenities_missing": "No amenities were listed.",
        "distance_unknown": "Distance to a requested place is unknown.",
    }
