"""logic_manager.py - domain brain of the hotel recommender (Phase 2, OOP).

Takes the hotel list from ai_manager, applies business rules, and decides an
outcome for each hotel: accepted, flagged or rejected. Every accepted hotel
gets a score out of 100 with a breakdown whose parts add up EXACTLY to the
total, and a plain-English reason for every part.

Rules of this layer (from the project brief):
  - Object-oriented: no stand-alone functions, behaviour lives in classes.
  - No print() here. Methods return data; the output layer does display.
  - No API calls here. ai_manager owns the API; data_manager owns files.
  - Input data is never modified; every method returns copies.

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

Class overview:
  ScoringConfig      business-rule constants (tune here)
  DataUtils          small static helpers (numbers, text matching, formatting)
  PreferenceParser   turns the user's free text into checkable amenities
  Requirements       what the user asked for + points per category
  HotelFacts         reads facts about one hotel (distance, amenities)
  HotelValidator     drops unusable hotels and attaches data-quality flags
  FilterRule (ABC)   one mandatory rule      -> BudgetRule, RatingRule,
                                                DistanceRule
  HotelFilter        applies a list of FilterRule objects
  ScoreComponent(ABC) one scored category    -> RatingComponent,
                                                PriceComponent,
                                                LocationComponent,
                                                PreferencesComponent,
                                                BonusComponent
  HotelScorer        applies a list of ScoreComponent objects
  HotelRanker        ranks and picks the top hotels
  LogicManager       runs the whole pipeline
"""
import re
from abc import ABC, abstractmethod


# Business-rule constants (tune here, not inside the methods)
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


# Small helpers
class DataUtils:
    """Stateless helpers shared by the other classes."""

    @staticmethod
    def norm_name(name):
        """Normalise a hotel name for duplicate detection and stable sorting."""
        return " ".join(str(name).lower().split())

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
        return any(DataUtils.has_term(text, term) for term in terms)

    @staticmethod
    def round_half_up(value):
        return int(value + 0.5)

    @staticmethod
    def money(value):
        return "S$%g" % value

    @staticmethod
    def metres(value):
        return "{:,} m".format(int(round(value)))


# User preference text -> checkable amenities
class PreferenceParser:
    """Splits the user's free text into amenity checks we can verify and
    phrases we cannot verify from hotel data (e.g. '3 beds', 'quiet room')."""

    @staticmethod
    def _split_phrases(text):
        parts = re.split(r",|;|&|\band\b|\bplus\b|\bwith\b", text or "",
                         flags=re.IGNORECASE)
        return [part.strip() for part in parts if part and part.strip()]

    @staticmethod
    def _mentions_target(phrase, targets):
        """True if the phrase is about one of the places the AI extracted."""
        words = set(re.findall(r"[a-z0-9]+", phrase.lower()))
        for target in targets:
            key = (set(re.findall(r"[a-z0-9]+", target.lower()))
                   - ScoringConfig.GENERIC_PLACE_WORDS)
            if key and key & words:
                return True
        return False

    def parse(self, text, targets):
        """Return (checks, unverified)."""
        checks = []
        unverified = []
        for phrase in self._split_phrases(text):
            lowered = phrase.lower()
            label = None
            for group_label, triggers, _terms in ScoringConfig.PREFERENCE_GROUPS:
                if DataUtils.has_any(lowered, triggers):
                    label = group_label
                    break
            if label:
                if label not in checks:
                    checks.append(label)
            elif (targets
                  and DataUtils.has_any(lowered, ScoringConfig.PROXIMITY_WORDS)
                  and self._mentions_target(lowered, targets)):
                continue          # handled by the Location category
            else:
                unverified.append(phrase)
        return checks, unverified


# 0. Requirements - what the user actually asked for
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


# Facts about one hotel
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


# 1. Validation
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


# 2. Filtering
class FilterRule(ABC):
    """Contract for one mandatory rule. Add a new rule by adding a subclass;
    HotelFilter does not need to change."""

    @abstractmethod
    def check(self, hotel, requirements):
        """Return a reason string if the rule is violated, else None."""


class BudgetRule(FilterRule):
    def check(self, hotel, requirements):
        price = hotel["price_per_night_sgd"]
        budget_max = requirements.budget_max
        if budget_max is not None and price > budget_max:
            return "%s per night is above your maximum budget of %s." % (
                DataUtils.money(price), DataUtils.money(budget_max))
        return None


class RatingRule(FilterRule):
    def check(self, hotel, requirements):
        rating = hotel.get("rating")
        minimum = ScoringConfig.MIN_ACCEPTABLE_RATING
        if DataUtils.is_number(rating) and rating < minimum:
            return ("Customer review rating %.1f/5 is below the minimum of "
                    "%.1f." % (rating, minimum))
        return None


class DistanceRule(FilterRule):
    def check(self, hotel, requirements):
        for target in requirements.targets:
            distance = HotelFacts.distance_for(hotel, target)
            if distance is not None and distance > ScoringConfig.MAX_NEAR_DISTANCE_M:
                return "%s from %s is too far to count as near." % (
                    DataUtils.metres(distance), target)
        return None


class HotelFilter:
    """Splits hotels into (kept, rejected) using a list of FilterRule objects.

    The budget comes from the user's input, not a hard-coded number.
    budget_min is deliberately not a hard rule: a cheaper hotel that meets
    everything else is not a worse result.
    Rejected hotels carry a 'reject_reason' so it can be shown or stored.
    Rules run in order; the first violated rule gives the reason.
    """

    def __init__(self, rules=None):
        self._rules = rules if rules is not None else [
            BudgetRule(), RatingRule(), DistanceRule()]

    def _rejection_reason(self, hotel, requirements):
        for rule in self._rules:
            reason = rule.check(hotel, requirements)
            if reason:
                return reason
        return None

    def filter(self, hotels, requirements):
        kept = []
        rejected = []
        for hotel in hotels:
            reason = self._rejection_reason(hotel, requirements)
            result = dict(hotel)
            if reason:
                result["outcome"] = "rejected"
                result["reject_reason"] = reason
                rejected.append(result)
            else:
                result["outcome"] = "flagged" if hotel.get("flags") else "accepted"
                kept.append(result)
        return kept, rejected


# 3. Scoring
# Each component's evaluate() returns (share of its points 0..1, reason text).
class ScoreComponent(ABC):
    """Contract for one scored category. Add a new category by adding a
    subclass; HotelScorer does not need to change."""

    key = None

    def applies(self, requirements):
        """Is this category scored for this search?"""
        return True

    def max_points(self, requirements):
        return requirements.maxima[self.key]

    @abstractmethod
    def evaluate(self, hotel, requirements):
        """Return (share 0..1, reason text)."""

    def score_line(self, hotel, requirements):
        max_points = self.max_points(requirements)
        share, reason = self.evaluate(hotel, requirements)
        points = min(
            max(DataUtils.round_half_up(share * max_points), 0), max_points)
        return {
            "key": self.key,
            "category": ScoringConfig.LABELS[self.key],
            "points": points,
            "max": max_points,
            "reason": reason,
        }


class RatingComponent(ScoreComponent):
    key = "rating"

    def evaluate(self, hotel, requirements):
        rating = hotel.get("rating")
        if not DataUtils.is_number(rating):
            return 0.5, ("No customer review rating was available, so neutral "
                         "points were given.")
        floor = ScoringConfig.RATING_FLOOR
        ceiling = ScoringConfig.RATING_CEILING
        share = (rating - floor) / (ceiling - floor)
        share = min(max(share, 0.0), 1.0)
        band = ScoringConfig.RATING_BELOW
        for threshold, name in ScoringConfig.RATING_BANDS:
            if rating >= threshold:
                band = name
                break
        return share, ("Customer review rating %.1f/5 (%s). This is the "
                       "average score from guest reviews, not the hotel's "
                       "number of stars." % (rating, band))


class PriceComponent(ScoreComponent):
    key = "price"

    def evaluate(self, hotel, requirements):
        price = hotel["price_per_night_sgd"]
        budget_min = requirements.budget_min
        budget_max = requirements.budget_max
        if budget_max is None or budget_max <= 0:
            return 0.5, ("%s per night. No valid budget was given, so neutral "
                         "points were given." % DataUtils.money(price))

        full_ratio = ScoringConfig.PRICE_FULL_POINTS_RATIO
        ratio = price / budget_max
        if ratio <= full_ratio:
            share = 1.0
            note = "well within your budget"
        else:
            span = 1.0 - full_ratio
            share = 1.0 - (min(ratio, 1.0) - full_ratio) / span * (
                1.0 - ScoringConfig.PRICE_MIN_SHARE_AT_MAX)
            note = "within budget but near the top of your range"
        if budget_min is not None and price < budget_min:
            note += ", and below your minimum"

        if budget_min is not None:
            budget_text = "%s-%s" % (DataUtils.money(budget_min),
                                     DataUtils.money(budget_max))
        else:
            budget_text = "up to %s" % DataUtils.money(budget_max)
        return share, "%s per night, %s (budget %s)." % (
            DataUtils.money(price), note, budget_text)


class LocationComponent(ScoreComponent):
    key = "location"

    def applies(self, requirements):
        return "location" in requirements.maxima

    @staticmethod
    def _distance_band(distance):
        for limit, share, label in ScoringConfig.DISTANCE_BANDS:
            if distance <= limit:
                return share, label
        return ScoringConfig.DISTANCE_BEYOND

    def evaluate(self, hotel, requirements):
        shares = []
        parts = []
        for target in requirements.targets:
            distance = HotelFacts.distance_for(hotel, target)
            if distance is None:
                shares.append(0.0)
                parts.append("Distance to %s is unknown" % target)
                continue
            share, label = self._distance_band(distance)
            shares.append(share)
            parts.append("%s from %s (%s)" % (
                DataUtils.metres(distance), target, label))
        return sum(shares) / len(shares), "; ".join(parts) + "."


class PreferencesComponent(ScoreComponent):
    key = "preferences"

    def applies(self, requirements):
        return "preferences" in requirements.maxima

    def evaluate(self, hotel, requirements):
        met, missing = HotelFacts.amenity_matches(hotel, requirements)
        share = len(met) / len(requirements.pref_checks)
        parts = []
        if met:
            parts.append("Has: " + ", ".join(met) + ".")
        if missing:
            parts.append("Not listed: " + ", ".join(missing) + ".")
        return share, " ".join(parts)


class BonusComponent(ScoreComponent):
    """Multi-condition rule: every condition must hold at the same time."""

    key = "bonus"

    def max_points(self, requirements):
        return ScoringConfig.BONUS_POINTS

    def evaluate(self, hotel, requirements):
        ok_texts = []
        fail_texts = []

        min_rating = ScoringConfig.BONUS_MIN_RATING
        max_distance = ScoringConfig.BONUS_MAX_DISTANCE_M

        rating = hotel.get("rating")
        if DataUtils.is_number(rating) and rating >= min_rating:
            ok_texts.append("customer review rating %.1f (needs %.1f or more)"
                            % (rating, min_rating))
        else:
            shown = "%.1f" % rating if DataUtils.is_number(rating) else "unknown"
            fail_texts.append("customer review rating of %.1f or more (this "
                              "hotel: %s)" % (min_rating, shown))

        budget_max = requirements.budget_max
        if budget_max is not None and hotel["price_per_night_sgd"] <= budget_max:
            ok_texts.append("price within budget")
        else:
            fail_texts.append("price within budget")

        targets = requirements.targets
        if targets:
            far = [t for t in targets
                   if HotelFacts.distance_for(hotel, t) is None
                   or HotelFacts.distance_for(hotel, t) > max_distance]
            if not far:
                ok_texts.append("within %d m of %s"
                                % (max_distance, ", ".join(targets)))
            else:
                fail_texts.append("within %d m of %s"
                                  % (max_distance, ", ".join(far)))

        if requirements.pref_checks:
            _met, missing = HotelFacts.amenity_matches(hotel, requirements)
            if not missing:
                ok_texts.append("has every amenity you asked for")
            else:
                fail_texts.append("amenities not listed: " + ", ".join(missing))

        if not fail_texts:
            return 1.0, "Awarded because: " + "; ".join(ok_texts) + "."
        return 0.0, ("Not awarded. All conditions must hold together. "
                     "Still needed: " + "; ".join(fail_texts) + ".")


class HotelScorer:
    """Returns a copy of the hotel with 'score' (out of 100), 'verdict' and
    'breakdown': a list of {category, points, max, reason} whose points add
    up exactly to 'score'."""

    def __init__(self, components=None):
        self._components = components if components is not None else [
            RatingComponent(), PriceComponent(), LocationComponent(),
            PreferencesComponent(), BonusComponent()]

    @staticmethod
    def _verdict(score):
        for threshold, label in ScoringConfig.VERDICTS:
            if score >= threshold:
                return label
        return ScoringConfig.VERDICT_LOW

    def score(self, hotel, requirements):
        breakdown = [component.score_line(hotel, requirements)
                     for component in self._components
                     if component.applies(requirements)]

        score = sum(line["points"] for line in breakdown)
        scored = dict(hotel)
        scored["score"] = score
        scored["score_max"] = (ScoringConfig.BASE_POINTS
                               + ScoringConfig.BONUS_POINTS)
        scored["verdict"] = self._verdict(score)
        scored["breakdown"] = breakdown
        return scored


# 4 and 5. Ranking and top picks
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


# Entry point for the rest of the system
class LogicManager:
    """Runs the full logic pipeline. The collaborators are created here (or
    passed in), so they can be swapped without changing this class."""

    def __init__(self, validator=None, hotel_filter=None, scorer=None,
                 ranker=None):
        self._validator = validator or HotelValidator()
        self._filter = hotel_filter or HotelFilter()
        self._scorer = scorer or HotelScorer()
        self._ranker = ranker or HotelRanker()

    def process_hotels(self, ai_output, record):
        """Does not modify ai_output or record.

        Returns a dict:
          top_hotels      - up to 3 ranked hotels, each with score, verdict,
                            breakdown
          rejected_hotels - hotels removed, each with 'reject_reason'
          requirements    - what was scored and what could not be checked
          summary         - counts, so the output layer can explain a short
                            result
        """
        requirements = Requirements(ai_output, record)
        valid = self._validator.validate(ai_output)
        kept, rejected = self._filter.filter(valid, requirements)
        scored = [self._scorer.score(hotel, requirements) for hotel in kept]
        top = self._ranker.top(self._ranker.rank(scored))

        received = 0
        if (isinstance(ai_output, dict)
                and isinstance(ai_output.get("hotels"), list)):
            received = len(ai_output["hotels"])
        return {
            "top_hotels": top,
            "rejected_hotels": rejected,
            "requirements": requirements.to_dict(),
            "summary": {
                "received": received,
                "valid": len(valid),
                "rejected": len(rejected),
                "returned": len(top),
            },
        }