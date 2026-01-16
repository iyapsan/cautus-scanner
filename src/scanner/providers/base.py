"""
Abstract base interfaces for all providers.

These are re-exported from models.py to keep Protocol definitions in one place.
"""

from scanner.models import (
    FundamentalsProvider,
    MarketDataProvider,
    NewsProvider,
    UniverseProvider,
)

__all__ = [
    "MarketDataProvider",
    "NewsProvider",
    "FundamentalsProvider",
    "UniverseProvider",
]
