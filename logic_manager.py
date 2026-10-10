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


# 2. filter_hotels
def _rejection_reason(hotel, requirements):
    """Return a reason string if a mandatory rule is violated, else None."""
    price = hotel["price_per_night_sgd"]
    budget_max = requirements["budget_max"]
    if budget_max is not None and price > budget_max:
        return "%s per night is above your maximum budget of %s." % (
            _money(price), _money(budget_max))

    rating = hotel.get("rating")
    if _is_number(rating) and rating < MIN_ACCEPTABLE_RATING:
        return ("Customer review rating %.1f/5 is below the minimum of "
                "%.1f." % (rating, MIN_ACCEPTABLE_RATING))

    for target in requirements["targets"]:
        distance = _distance_for(hotel, target)
        if distance is not None and distance > MAX_NEAR_DISTANCE_M:
            return "%s from %s is too far to count as near." % (
                _metres(distance), target)
    return None


def filter_hotels(hotels, requirements):
    """Split hotels into (kept, rejected) using the mandatory rules.

    The budget comes from the user's input, not a hard-coded number.
    budget_min is deliberately not a hard rule: a cheaper hotel that meets
    everything else is not a worse result.
    Rejected hotels carry a 'reject_reason' so it can be shown or stored.
    """
    kept = []
    rejected = []
    for hotel in hotels:
        reason = _rejection_reason(hotel, requirements)
        result = dict(hotel)
        if reason:
            result["outcome"] = "rejected"
            result["reject_reason"] = reason
            rejected.append(result)
        else:
            result["outcome"] = "flagged" if hotel.get("flags") else "accepted"
            kept.append(result)
    return kept, rejected


# 3. calculate_score
# Each component returns (share of its points 0..1, reason text).
def _rating_component(hotel):
    rating = hotel.get("rating")
    if not _is_number(rating):
        return 0.5, ("No customer review rating was available, so neutral "
                     "points were given.")
    share = (rating - RATING_FLOOR) / (RATING_CEILING - RATING_FLOOR)
    share = min(max(share, 0.0), 1.0)
    band = RATING_BELOW
    for threshold, name in RATING_BANDS:
        if rating >= threshold:
            band = name
            break
    return share, ("Customer review rating %.1f/5 (%s). This is the average "
                   "score from guest reviews, not the hotel's number of stars."
                   % (rating, band))


def _price_component(hotel, requirements):
    price = hotel["price_per_night_sgd"]
    budget_min = requirements["budget_min"]
    budget_max = requirements["budget_max"]
    if budget_max is None or budget_max <= 0:
        return 0.5, ("%s per night. No valid budget was given, so neutral "
                     "points were given." % _money(price))

    ratio = price / budget_max
    if ratio <= PRICE_FULL_POINTS_RATIO:
        share = 1.0
        note = "well within your budget"
    else:
        span = 1.0 - PRICE_FULL_POINTS_RATIO
        share = 1.0 - (min(ratio, 1.0) - PRICE_FULL_POINTS_RATIO) / span * (
            1.0 - PRICE_MIN_SHARE_AT_MAX)
        note = "within budget but near the top of your range"
    if budget_min is not None and price < budget_min:
        note += ", and below your minimum"

    if budget_min is not None:
        budget_text = "%s-%s" % (_money(budget_min), _money(budget_max))
    else:
        budget_text = "up to %s" % _money(budget_max)
    return share, "%s per night, %s (budget %s)." % (
        _money(price), note, budget_text)


def _location_component(hotel, requirements):
    shares = []
    parts = []
    for target in requirements["targets"]:
        distance = _distance_for(hotel, target)
        if distance is None:
            shares.append(0.0)
            parts.append("Distance to %s is unknown" % target)
            continue
        share, label = _distance_band(distance)
        shares.append(share)
        parts.append("%s from %s (%s)" % (_metres(distance), target, label))
    return sum(shares) / len(shares), "; ".join(parts) + "."


def _preferences_component(hotel, requirements):
    met, missing = _amenity_matches(hotel, requirements)
    share = len(met) / len(requirements["pref_checks"])
    parts = []
    if met:
        parts.append("Has: " + ", ".join(met) + ".")
    if missing:
        parts.append("Not listed: " + ", ".join(missing) + ".")
    return share, " ".join(parts)


def _bonus_component(hotel, requirements):
    """Multi-condition rule: every condition must hold at the same time."""
    ok_texts = []
    fail_texts = []

    rating = hotel.get("rating")
    if _is_number(rating) and rating >= BONUS_MIN_RATING:
        ok_texts.append("customer review rating %.1f (needs %.1f or more)"
                        % (rating, BONUS_MIN_RATING))
    else:
        shown = "%.1f" % rating if _is_number(rating) else "unknown"
        fail_texts.append("customer review rating of %.1f or more (this "
                          "hotel: %s)" % (BONUS_MIN_RATING, shown))

    budget_max = requirements["budget_max"]
    if budget_max is not None and hotel["price_per_night_sgd"] <= budget_max:
        ok_texts.append("price within budget")
    else:
        fail_texts.append("price within budget")

    targets = requirements["targets"]
    if targets:
        far = [t for t in targets
               if _distance_for(hotel, t) is None
               or _distance_for(hotel, t) > BONUS_MAX_DISTANCE_M]
        if not far:
            ok_texts.append("within %d m of %s"
                            % (BONUS_MAX_DISTANCE_M, ", ".join(targets)))
        else:
            fail_texts.append("within %d m of %s"
                              % (BONUS_MAX_DISTANCE_M, ", ".join(far)))

    if requirements["pref_checks"]:
        _met, missing = _amenity_matches(hotel, requirements)
        if not missing:
            ok_texts.append("has every amenity you asked for")
        else:
            fail_texts.append("amenities not listed: " + ", ".join(missing))

    if not fail_texts:
        return 1.0, "Awarded because: " + "; ".join(ok_texts) + "."
    return 0.0, ("Not awarded. All conditions must hold together. "
                 "Still needed: " + "; ".join(fail_texts) + ".")


def _make_line(key, share, reason, max_points):
    points = min(max(_round_half_up(share * max_points), 0), max_points)
    return {
        "key": key,
        "category": LABELS[key],
        "points": points,
        "max": max_points,
        "reason": reason,
    }


def calculate_score(hotel, requirements):
    """Return a copy of the hotel with 'score' (out of 100), 'verdict' and
    'breakdown': a list of {category, points, max, reason} whose points add
    up exactly to 'score'."""
    maxima = requirements["maxima"]
    breakdown = []

    share, reason = _rating_component(hotel)
    breakdown.append(_make_line("rating", share, reason, maxima["rating"]))

    share, reason = _price_component(hotel, requirements)
    breakdown.append(_make_line("price", share, reason, maxima["price"]))

    if "location" in maxima:
        share, reason = _location_component(hotel, requirements)
        breakdown.append(
            _make_line("location", share, reason, maxima["location"]))

    if "preferences" in maxima:
        share, reason = _preferences_component(hotel, requirements)
        breakdown.append(
            _make_line("preferences", share, reason, maxima["preferences"]))

    share, reason = _bonus_component(hotel, requirements)
    breakdown.append(_make_line("bonus", share, reason, BONUS_POINTS))

    score = sum(line["points"] for line in breakdown)
    scored = dict(hotel)
    scored["score"] = score
    scored["score_max"] = BASE_POINTS + BONUS_POINTS
    scored["verdict"] = _verdict(score)
    scored["breakdown"] = breakdown
    return scored
