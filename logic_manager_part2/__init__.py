"""logic_managerpart2 package: business rules of the hotel recommender.

One class per file. Only LogicManager knows the other classes; the rest of the
app uses just LogicManager."""
from .logic_manager import LogicManager

__all__ = ["LogicManager"]
