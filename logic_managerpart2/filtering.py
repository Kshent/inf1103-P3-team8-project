"""filtering.py - Mandatory rules and the filter that applies them."""
from abc import ABC, abstractmethod
from .config import ScoringConfig
from .utils import DataUtils
from .facts import HotelFacts


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
