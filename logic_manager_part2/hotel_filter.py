"""hotel_filter.py - HotelFilter: the gatekeeper for the mandatory rules."""


class HotelFilter:
    """Decides whether a hotel breaks a mandatory rule.

    The budget comes from the user's input, not a hard-coded number.
    budget_min is deliberately not a hard rule: a cheaper hotel that meets
    everything else is not a worse result.

    It never talks to any other class: LogicManager hands it a hotel's facts
    (plain data) and takes the answer back."""

    def __init__(self, settings, budget_max, targets):
        self.min_acceptable_rating = settings["min_acceptable_rating"]
        self.max_near_distance_m = settings["max_near_distance_m"]
        self.budget_max = budget_max
        self.targets = targets

    # Small helpers (own copies on purpose, so this class stands alone)
    @staticmethod
    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def money(value):
        return "S$%g" % value

    @staticmethod
    def metres(value):
        return "{:,} m".format(int(round(value)))

    # The three rules; each returns a reason string, or None if it passes
    def check_budget(self, facts):
        price = facts["price"]
        if self.budget_max is not None and price > self.budget_max:
            return "%s per night is above your maximum budget of %s." % (
                self.money(price), self.money(self.budget_max))
        return None

    def check_rating(self, facts):
        rating = facts["rating"]
        if self.is_number(rating) and rating < self.min_acceptable_rating:
            return ("Customer review rating %.1f/5 is below the minimum of "
                    "%.1f." % (rating, self.min_acceptable_rating))
        return None

    def check_distance(self, facts):
        for target, distance in zip(self.targets, facts["distances"]):
            if distance is not None and distance > self.max_near_distance_m:
                return "%s from %s is too far to count as near." % (
                    self.metres(distance), target)
        return None

    def rejection_reason(self, facts):
        """Return a reason string if a mandatory rule is violated, else None.
        Rules run in order; the first violated rule gives the reason."""
        for rule in (self.check_budget, self.check_rating,
                     self.check_distance):
            reason = rule(facts)
            if reason:
                return reason
        return None
