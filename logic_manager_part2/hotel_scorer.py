"""hotel_scorer.py - HotelScorer: scores each hotel out of 100, then ranks them."""


class HotelScorer:
    """Scores a hotel out of 100 with a breakdown whose parts add up EXACTLY to
    the total, and ranks scored hotels.

    Each scored category is one method returning (share of its points 0..1,
    reason text). A category that does not apply (no place named, nothing
    checkable in the preferences) is not scored; its points are shared across
    the scored categories (see Requirements), so the total is still out of 100.

    It never talks to any other class: LogicManager hands it a hotel's facts
    (plain data) and takes the answer back."""

    def __init__(self, settings, maxima, targets, pref_checks, budget_min,
                 budget_max):
        # From the user's search
        self.maxima = maxima
        self.targets = targets
        self.pref_checks = pref_checks
        self.budget_min = budget_min
        self.budget_max = budget_max
        # From the rulebook
        self.base_points = settings["base_points"]
        self.bonus_points = settings["bonus_points"]
        self.allocated_weights = settings.get("allocated_weights", {})
        self.redistribute_unscored = settings.get("redistribute_unscored", True)
        self.labels = settings["labels"]
        self.bonus_min_rating = settings["bonus_min_rating"]
        self.bonus_max_distance_m = settings["bonus_max_distance_m"]
        self.top_n = settings["top_n"]
        self.rating_floor = settings["rating_floor"]
        self.rating_ceiling = settings["rating_ceiling"]
        self.rating_bands = settings["rating_bands"]
        self.rating_below = settings["rating_below"]
        self.distance_bands = settings["distance_bands"]
        self.distance_beyond = settings["distance_beyond"]
        self.price_full_points_ratio = settings["price_full_points_ratio"]
        self.price_min_share_at_max = settings["price_min_share_at_max"]
        self.verdicts = settings["verdicts"]
        self.verdict_low = settings["verdict_low"]
        # Results of the last ranking
        self.ranked_hotels = []
        self.top_hotels = []

    # Small helpers (own copies on purpose, so this class stands alone)
    @staticmethod
    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def norm_name(name):
        """Normalise a hotel name for duplicate detection and stable sorting."""
        return " ".join(str(name).lower().split())

    @staticmethod
    def round_half_up(value):
        return int(value + 0.5)

    @staticmethod
    def money(value):
        return "S$%g" % value

    @staticmethod
    def metres(value):
        return "{:,} m".format(int(round(value)))

    # Lookups in the rulebook tables
    def verdict_for(self, score):
        for threshold, label in self.verdicts:
            if score >= threshold:
                return label
        return self.verdict_low

    def rating_band(self, rating):
        for threshold, name in self.rating_bands:
            if rating >= threshold:
                return name
        return self.rating_below

    def distance_band(self, distance):
        for limit, share, label in self.distance_bands:
            if distance <= limit:
                return share, label
        return self.distance_beyond

    # The scored categories
    def rating_component(self, facts):
        rating = facts["rating"]
        if not self.is_number(rating):
            return 0.5, ("No customer review rating was available, so neutral "
                         "points were given.")
        share = (rating - self.rating_floor) / (
            self.rating_ceiling - self.rating_floor)
        share = min(max(share, 0.0), 1.0)
        band = self.rating_band(rating)
        return share, ("Customer review rating %.1f/5 (%s). This is the "
                       "average score from guest reviews, not the hotel's "
                       "number of stars." % (rating, band))

    def price_component(self, facts):
        price = facts["price"]
        if self.budget_max is None or self.budget_max <= 0:
            return 0.5, ("%s per night. No valid budget was given, so neutral "
                         "points were given." % self.money(price))

        ratio = price / self.budget_max
        if ratio <= self.price_full_points_ratio:
            share = 1.0
            note = "well within your budget"
        else:
            span = 1.0 - self.price_full_points_ratio
            share = 1.0 - (min(ratio, 1.0) - self.price_full_points_ratio
                           ) / span * (1.0 - self.price_min_share_at_max)
            note = "within budget but near the top of your range"
        if self.budget_min is not None and price < self.budget_min:
            note += ", and below your minimum"

        if self.budget_min is not None:
            budget_text = "%s-%s" % (self.money(self.budget_min),
                                     self.money(self.budget_max))
        else:
            budget_text = "up to %s" % self.money(self.budget_max)
        return share, "%s per night, %s (budget %s)." % (
            self.money(price), note, budget_text)

    def location_component(self, facts):
        shares = []
        parts = []
        for target, distance in zip(self.targets, facts["distances"]):
            if distance is None:
                shares.append(0.0)
                parts.append("Distance to %s is unknown" % target)
                continue
            share, label = self.distance_band(distance)
            shares.append(share)
            parts.append("%s from %s (%s)" % (
                self.metres(distance), target, label))
        return sum(shares) / len(shares), "; ".join(parts) + "."

    def preferences_component(self, facts):
        met = facts["met"]
        missing = facts["missing"]
        share = len(met) / len(self.pref_checks)
        parts = []
        if met:
            parts.append("Has: " + ", ".join(met) + ".")
        if missing:
            parts.append("Not listed: " + ", ".join(missing) + ".")
        return share, " ".join(parts)

    def bonus_component(self, facts):
        """Multi-condition rule: every condition must hold at the same time."""
        ok_texts = []
        fail_texts = []

        rating = facts["rating"]
        if self.is_number(rating) and rating >= self.bonus_min_rating:
            ok_texts.append("customer review rating %.1f (needs %.1f or more)"
                            % (rating, self.bonus_min_rating))
        else:
            shown = "%.1f" % rating if self.is_number(rating) else "unknown"
            fail_texts.append("customer review rating of %.1f or more (this "
                              "hotel: %s)" % (self.bonus_min_rating, shown))

        if self.budget_max is not None and facts["price"] <= self.budget_max:
            ok_texts.append("price within budget")
        else:
            fail_texts.append("price within budget")

        if self.targets:
            far = [target for target, distance
                   in zip(self.targets, facts["distances"])
                   if distance is None
                   or distance > self.bonus_max_distance_m]
            if not far:
                ok_texts.append("within %d m of %s" % (
                    self.bonus_max_distance_m, ", ".join(self.targets)))
            else:
                fail_texts.append("within %d m of %s" % (
                    self.bonus_max_distance_m, ", ".join(far)))

        if self.pref_checks:
            missing = facts["missing"]
            if not missing:
                ok_texts.append("has every amenity you asked for")
            else:
                fail_texts.append("amenities not listed: " + ", ".join(missing))

        if not fail_texts:
            return 1.0, "Awarded because: " + "; ".join(ok_texts) + "."
        return 0.0, ("Not awarded. All conditions must hold together. "
                     "Still needed: " + "; ".join(fail_texts) + ".")

    # Putting the score together
    def make_line(self, key, share, reason, max_points):
        points = min(max(self.round_half_up(share * max_points), 0),
                     max_points)
        return {
            "key": key,
            "category": self.labels[key],
            "points": points,
            "max": max_points,
            "reason": reason,
        }

    def calculate_score(self, facts):
        """Return the score fields for one hotel: 'score' (out of 100),
        'score_max', 'verdict' and 'breakdown' (a list of {category, points,
        max, reason} whose points add up exactly to 'score')."""
        breakdown = []

        share, reason = self.rating_component(facts)
        breakdown.append(self.make_line(
            "rating", share, reason, self.maxima["rating"]))

        share, reason = self.price_component(facts)
        breakdown.append(self.make_line(
            "price", share, reason, self.maxima["price"]))

        
        # Location scoring
        if "location" in self.maxima:
            share, reason = self.location_component(facts)
            breakdown.append(self.make_line(
                "location", share, reason, self.maxima["location"]
            ))

        elif not self.redistribute_unscored:
            breakdown.append(self.make_line(
                "location",
                0.0,
                "Not scored: no requested nearby place.",
                self.allocated_weights["location"]
            ))

        # Preferences scoring
        if "preferences" in self.maxima:
            share, reason = self.preferences_component(facts)
            breakdown.append(self.make_line(
                "preferences", share, reason,
                self.maxima["preferences"]
            ))

        elif not self.redistribute_unscored:
            breakdown.append(self.make_line(
                "preferences",
                0.0,
                "Not scored: no checkable amenity was requested.",
                self.allocated_weights["preferences"]
            ))

        share, reason = self.bonus_component(facts)
        breakdown.append(self.make_line(
            "bonus", share, reason, self.bonus_points))

        score = sum(line["points"] for line in breakdown)
        return {
            "score": score,
            "score_max": self.base_points + self.bonus_points,
            "verdict": self.verdict_for(score),
            "breakdown": breakdown,
        }

    # Ranking (works on hotels as plain dicts)
    def rank_hotels(self, hotels):
        """Sort by score (high to low). Ties go to the higher customer rating,
        then the lower price, then the name, so the same input always gives
        the same order."""
        def sort_key(hotel):
            rating = hotel.get("rating")
            return (-hotel["score"],
                    -(rating if self.is_number(rating) else 0),
                    hotel["price_per_night_sgd"],
                    self.norm_name(hotel["name"]))
        self.ranked_hotels = sorted(hotels, key=sort_key)
        return self.ranked_hotels

    def get_top_three(self, ranked_hotels):
        """Return up to 'top_n' distinct hotels from an already-ranked list.
        Returns fewer if fewer exist; never pads or crashes."""
        top = []
        seen = set()
        for hotel in ranked_hotels:
            key = self.norm_name(hotel["name"])
            if key in seen:
                continue
            seen.add(key)
            entry = dict(hotel)
            entry["rank"] = len(top) + 1
            top.append(entry)
            if len(top) == self.top_n:
                break
        self.top_hotels = top
        return top
