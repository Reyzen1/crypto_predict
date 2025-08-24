# File: backend\app\models\watchlist\__init__.py
# SQLAlchemy model for module initialization

from .watchlist import Watchlist, WatchlistItem
from .suggestion import AISuggestion
from .review import SuggestionReview

__all__ = ["Watchlist", "WatchlistItem", "AISuggestion", "SuggestionReview"]
