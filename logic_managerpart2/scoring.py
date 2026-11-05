"""scoring.py - Scored categories (components) and the scorer that applies them."""
from abc import ABC, abstractmethod
from .config import ScoringConfig
from .utils import DataUtils
from .facts import HotelFacts


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
