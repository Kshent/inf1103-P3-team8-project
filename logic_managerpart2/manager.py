"""manager.py - Entry point: runs the whole logic pipeline."""
from .requirements import Requirements
from .validation import HotelValidator
from .filtering import HotelFilter
from .scoring import HotelScorer
from .ranking import HotelRanker


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
