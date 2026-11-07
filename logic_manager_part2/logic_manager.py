"""logic_manager.py - LogicManager: runs a search from start to finish.

Takes the hotel list from ai_manager, applies business rules, and decides an
outcome for each hotel: accepted, flagged or rejected. Every accepted hotel
gets a score out of 100 with a breakdown whose parts add up EXACTLY to the
total, and a plain-English reason for every part.

Rules of this layer (from the project brief):
  - Object-oriented, with one class per file.
  - No print() here. Methods return data; the output layer does display.
  - No API calls here. ai_manager owns the API; data_manager owns files.
  - Input data is never modified; every method returns copies.

About "rating": it is the CUSTOMER REVIEW rating (average of guest reviews),
as reported by the AI. It is never the hotel's number of stars.
"""
from .scoring_config import ScoringConfig
from .hotel import Hotel
from .requirements import Requirements
from .hotel_filter import HotelFilter
from .hotel_scorer import HotelScorer


class LogicManager:
    """The hub of the logic layer (a mediator).

    This is the ONLY class that knows the others exist. The other classes never
    import, create or call each other: each one returns its answer to
    LogicManager, which passes what the next class needs as plain data.
    LogicManager itself holds no business rules, only the order of the steps.
    """

    def __init__(self, config=None):
        self.config = config if config is not None else ScoringConfig()
        # Set up fresh for every search (see begin_search)
        self.requirements = None
        self.hotel_filter = None
        self.scorer = None
        self.hotels = []
        self.last_result = None

    def begin_search(self, ai_output, record):
        """Build this search's Requirements, HotelFilter and HotelScorer, so
        nothing carries over from the previous search."""
        self.requirements = Requirements(
            ai_output, record, self.config.requirements_settings())
        req = self.requirements
        self.hotel_filter = HotelFilter(
            self.config.filter_settings(), req.budget_max, req.targets)
        self.scorer = HotelScorer(
            self.config.scorer_settings(), req.maxima, req.targets,
            req.pref_checks, req.budget_min, req.budget_max)
        self.hotels = []

    def validate_hotels(self, ai_output):
        """Return the usable hotels (as Hotel objects) from the ai_manager
        result.

        ai_manager checks the structure. This checks usefulness: drops records
        without a name or a usable price, removes duplicate names, and attaches
        a 'flags' list for data that is missing or suspicious. Never raises.
        """
        valid = []
        if not isinstance(ai_output, dict):
            return valid
        raw_hotels = ai_output.get("hotels")
        if not isinstance(raw_hotels, list):
            return valid

        targets = self.requirements.targets
        seen = set()
        for raw in raw_hotels:
            if not Hotel.is_record(raw):
                continue
            hotel = Hotel(raw)
            if not hotel.is_usable():
                continue
            key = hotel.norm_key()
            if key in seen:
                continue
            seen.add(key)
            hotel.compute_flags(targets)
            valid.append(hotel)
        self.hotels = valid
        return valid

    def _facts_for(self, hotel):
        """Ask a Hotel for its facts, as plain data."""
        req = self.requirements
        return hotel.facts(
            req.targets, req.pref_checks,
            self.config.hotel_settings()["amenity_terms"])

    def filter_hotels(self, hotels):
        """Split hotels into (kept, rejected) using the mandatory rules.
        Rejected hotels carry a 'reject_reason' so it can be shown or stored."""
        kept = []
        rejected = []
        for hotel in hotels:
            reason = self.hotel_filter.rejection_reason(
                self._facts_for(hotel))
            if reason:
                hotel.mark_rejected(reason)
                rejected.append(hotel)
            else:
                hotel.mark_kept()
                kept.append(hotel)
        return kept, rejected

    def score_hotels(self, hotels):
        """Score every kept hotel and record the result on it."""
        for hotel in hotels:
            hotel.apply_score(
                self.scorer.calculate_score(self._facts_for(hotel)))
        return hotels

    def rank_and_select(self, scored_hotels):
        """Rank the scored hotels and pick the top three (as plain dicts)."""
        as_dicts = [hotel.to_dict() for hotel in scored_hotels]
        ranked = self.scorer.rank_hotels(as_dicts)
        return self.scorer.get_top_three(ranked)

    @staticmethod
    def count_received(ai_output):
        """How many hotels the AI sent."""
        if (isinstance(ai_output, dict)
                and isinstance(ai_output.get("hotels"), list)):
            return len(ai_output["hotels"])
        return 0

    def build_summary(self, ai_output, valid, rejected, top):
        """Counts, so the output layer can explain a short result."""
        return {
            "received": self.count_received(ai_output),
            "valid": len(valid),
            "rejected": len(rejected),
            "returned": len(top),
        }

    def process_hotels(self, ai_output, record):
        """Run the full logic pipeline. Does not modify ai_output or record.

        Returns a dict:
          top_hotels      - up to 3 ranked hotels, each with score, verdict,
                            breakdown
          rejected_hotels - hotels removed, each with 'reject_reason'
          requirements    - what was scored and what could not be checked
          summary         - counts, so the output layer can explain a short
                            result
        """
        self.begin_search(ai_output, record)
        valid = self.validate_hotels(ai_output)
        kept, rejected = self.filter_hotels(valid)
        scored = self.score_hotels(kept)
        top = self.rank_and_select(scored)

        self.last_result = {
            "top_hotels": top,
            "rejected_hotels": [hotel.to_dict() for hotel in rejected],
            "requirements": self.requirements.to_dict(),
            "summary": self.build_summary(ai_output, valid, rejected, top),
        }
        return self.last_result
