"""logic_manager.py - domain brain of the hotel recommender.

Takes the hotel list from ai_manager, applies business rules, and decides an
outcome for each hotel: accepted, flagged or rejected. Every accepted hotel
gets a score out of 100 with a breakdown whose parts add up EXACTLY to the
total, and a plain-English reason for every part.

Rules of this layer (from the project brief):
  - 100% procedural: functions only.
  - No print() here. Functions return data; the output layer does display.
  - No API calls here. ai_manager owns the API; data_manager owns files.
  - Input data is never modified; every function returns copies.

Scoring (always out of 100):
  Base points = 90, shared between these categories:
    Customer review rating  25   how well guests rated the hotel
    Price                   20   fit against the user's budget
    Location                25   distance to the places the user asked to be near
    Your preferences        20   requested amenities found in the hotel's amenities
  Top-match bonus = 10, awarded only when ALL of these hold at the same time
  (this is the multi-condition rule): rating >= 4.5, price within budget,
  within 300 m of every requested place, and every checkable amenity present.

  A category that does not apply (the user named no place, or nothing in their
  preferences can be checked against hotel data) is not scored. Its points are
  shared across the scored categories so the total is still out of 100.

About "rating": it is the CUSTOMER REVIEW rating (average of guest reviews),
as reported by the AI. It is never the hotel's number of stars.
"""
import re
# Business-rule constants (tune here, not inside the functions)
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
    ("high floor", ["high floor", "high floors", "high-floor", "upper floor"],
     ["high floor", "high floors", "high-floor", "upper floor"]),
    ("metro access", ["metro", "mrt", "subway", "public transport", "train"],
     ["metro", "mrt", "subway", "train", "public transport"]),
]

# Words that say nothing about WHICH place (ignored when matching a phrase
# like "near nanjing street" to the place the AI extracted)
GENERIC_PLACE_WORDS = {"road", "street", "st", "rd", "avenue", "ave", "the",
                       "of", "and", "near", "singapore"}

FLAG_MESSAGES = {
    "rating_missing": "No customer review rating was available.",
    "rating_may_be_stars": (
        "The rating is a whole number, so it may be a hotel's number of stars "
        "rather than an average of guest reviews. Please verify."),
    "amenities_missing": "No amenities were listed.",
    "distance_unknown": "Distance to a requested place is unknown.",
}

# Small helpers
def _norm_name(name):
    """Normalise a hotel name for duplicate detection and stable sorting."""
    return " ".join(str(name).lower().split())


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_list(value):
    return value if isinstance(value, list) else []


def _has_term(text, term):
    """Whole-word match, so 'spa' does not match 'spacious'."""
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def _has_any(text, terms):
    return any(_has_term(text, term) for term in terms)


def _round_half_up(value):
    return int(value + 0.5)


def _money(value):
    return "S$%g" % value


def _metres(value):
    return "{:,} m".format(int(round(value)))


def _proximity_targets(ai_output):
    """Places the user asked to be near, as extracted by the AI."""
    targets = []
    if not isinstance(ai_output, dict):
        return targets
    proximity = ai_output.get("proximity_preference")
    if not isinstance(proximity, dict) or proximity.get("specified") is not True:
        return targets
    for target in _as_list(proximity.get("preferences")):
        if isinstance(target, str) and target.strip():
            targets.append(target.strip())
    return targets


def _distance_for(hotel, target):
    """Distance in metres from this hotel to a target, or None if unknown."""
    for item in _as_list(hotel.get("distance_to_preferences")):
        if not isinstance(item, dict):
            continue
        name = item.get("target")
        if isinstance(name, str) and name.strip().lower() == target.lower():
            distance = item.get("distance_m")
            if _is_number(distance) and distance >= 0:
                return distance
            return None
    return None


def _mentions_target(phrase, targets):
    """True if the phrase is about one of the places the AI extracted."""
    words = set(re.findall(r"[a-z0-9]+", phrase.lower()))
    for target in targets:
        key = set(re.findall(r"[a-z0-9]+", target.lower())) - GENERIC_PLACE_WORDS
        if key and key & words:
            return True
    return False


def _split_phrases(text):
    parts = re.split(r",|;|&|\band\b|\bplus\b|\bwith\b", text or "",
                     flags=re.IGNORECASE)
    return [part.strip() for part in parts if part and part.strip()]


def _parse_preferences(text, targets):
    """Split the user's free text into amenity checks we can verify and
    phrases we cannot verify from hotel data (e.g. '3 beds', 'quiet room')."""
    checks = []
    unverified = []
    for phrase in _split_phrases(text):
        lowered = phrase.lower()
        label = None
        for group_label, triggers, _terms in PREFERENCE_GROUPS:
            if _has_any(lowered, triggers):
                label = group_label
                break
        if label:
            if label not in checks:
                checks.append(label)
        elif (targets and _has_any(lowered, PROXIMITY_WORDS)
              and _mentions_target(lowered, targets)):
            continue          # handled by the Location category
        else:
            unverified.append(phrase)
    return checks, unverified


def _allocate_maxima(active):
    """Share BASE_POINTS across the scored categories using whole numbers
    that add up to exactly BASE_POINTS."""
    total = sum(WEIGHTS[key] for key in active)
    raw = {key: WEIGHTS[key] * BASE_POINTS / total for key in active}
    maxima = {key: int(round(raw[key], 9)) for key in active}
    leftover = BASE_POINTS - sum(maxima.values())
    by_remainder = sorted(
        active,
        key=lambda key: (-(raw[key] - maxima[key]), CATEGORY_ORDER.index(key)))
    for key in by_remainder[:leftover]:
        maxima[key] += 1
    return maxima


def _verdict(score):
    for threshold, label in VERDICTS:
        if score >= threshold:
            return label
    return VERDICT_LOW


def _distance_band(distance):
    for limit, share, label in DISTANCE_BANDS:
        if distance <= limit:
            return share, label
    return DISTANCE_BEYOND


def _amenity_matches(hotel, requirements):
    """Return (met, missing): requested amenities this hotel has / lacks."""
    amenities = [str(item) for item in _as_list(hotel.get("amenities"))]
    terms_by_label = {label: terms for label, _t, terms in PREFERENCE_GROUPS}
    met = []
    missing = []
    for label in requirements["pref_checks"]:
        found = None
        for amenity in amenities:
            if _has_any(amenity.lower(), terms_by_label[label]):
                found = amenity
                break
        if found:
            met.append("%s (%s)" % (label, found))
        else:
            missing.append(label)
    return met, missing


# 0. build_requirements - what the user actually asked for
def build_requirements(ai_output, record):
    """Work out, once per search, what will be scored and how many points
    each category is worth. Returned as plain data so the output layer can
    explain it."""
    targets = _proximity_targets(ai_output)
    checks, unverified = _parse_preferences(
        record.get("preferences"), targets)

    budget_min = record.get("budget_min")
    budget_max = record.get("budget_max")

    active = ["rating", "price"]
    not_scored = []
    if targets:
        active.append("location")
    else:
        not_scored.append(
            "Location was not scored: you did not ask to be near a place.")
    if checks:
        active.append("preferences")
    else:
        not_scored.append(
            "Amenity preferences were not scored: nothing you asked for "
            "could be checked against the hotel data.")
    if not_scored:
        not_scored.append(
            "Points for unscored categories are shared across the scored "
            "ones, so every score is still out of 100.")

    return {
        "budget_min": budget_min if _is_number(budget_min) else None,
        "budget_max": budget_max if _is_number(budget_max) else None,
        "targets": targets,
        "pref_checks": checks,
        "unverified": unverified,
        "maxima": _allocate_maxima(active),
        "not_scored": not_scored,
    }

# 1. validate_hotels
def validate_hotels(ai_output):
    """Return the usable hotels from the ai_manager result.

    ai_manager checks the structure. This checks usefulness: drops records
    without a name or a usable price, removes duplicate names, and attaches a
    'flags' list for data that is missing or suspicious. Never raises.
    """
    if not isinstance(ai_output, dict):
        return []
    hotels = ai_output.get("hotels")
    if not isinstance(hotels, list):
        return []

    targets = _proximity_targets(ai_output)
    valid = []
    seen = set()
    for hotel in hotels:
        if not isinstance(hotel, dict):
            continue
        name = hotel.get("name")
        price = hotel.get("price_per_night_sgd")
        if not isinstance(name, str) or not name.strip():
            continue
        if not _is_number(price) or price <= 0:
            continue

        key = _norm_name(name)
        if key in seen:
            continue
        seen.add(key)

        flags = []
        rating = hotel.get("rating")
        if not _is_number(rating):
            flags.append("rating_missing")
        elif float(rating).is_integer():
            flags.append("rating_may_be_stars")
        if not _as_list(hotel.get("amenities")):
            flags.append("amenities_missing")
        if any(_distance_for(hotel, target) is None for target in targets):
            flags.append("distance_unknown")

        checked = dict(hotel)
        checked["flags"] = flags
        valid.append(checked)
    return valid