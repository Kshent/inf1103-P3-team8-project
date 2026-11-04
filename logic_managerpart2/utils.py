"""utils.py - Small stateless helpers shared by the other modules."""
import re


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
