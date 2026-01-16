"""
Two-tier caching for scanner performance.

- HistoricalDataCache: Pre-market cache for static data (30-day avg volume)
- ScannerResultsCache: Intraday per-symbol TTL-based cache
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scanner.models import MarketDataProvider, ScanResult

logger = logging.getLogger(__name__)


class HistoricalDataCache:
    """
    Pre-market cache for static data (doesn't change intraday).
    
    Populated once at ~4:00 AM or market open.
    Run warm() before market open to pre-compute all avg volumes.
    """

    def __init__(self) -> None:
        self.avg_volume: dict[str, float] = {}
        self._warmed_at: datetime | None = None

    def warm(self, symbols: list[str], provider: "MarketDataProvider") -> None:
        """
        Fetch 30-day history for all symbols. Run pre-market.

        Args:
            symbols: List of symbols to pre-compute
            provider: Market data provider for historical data
        """
        logger.info(f"Warming historical cache for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                volumes = provider.get_historical_daily_volume(symbol, lookback_days=30)
                if volumes:
                    self.avg_volume[symbol] = sum(volumes) / len(volumes)
            except Exception as e:
                logger.warning(f"Failed to warm cache for {symbol}: {e}")

        self._warmed_at = datetime.now(timezone.utc)
        logger.info(f"Cache warmed: {len(self.avg_volume)} symbols")

    def get_avg_volume(self, symbol: str) -> float | None:
        """Get pre-computed average volume for symbol."""
        return self.avg_volume.get(symbol.upper())

    @property
    def is_warm(self) -> bool:
        """True if cache has been warmed today."""
        if self._warmed_at is None:
            return False
        # Consider stale after 24 hours
        return datetime.now(timezone.utc) - self._warmed_at < timedelta(hours=24)


class ScannerResultsCache:
    """Per-symbol, TTL-based results cache for intraday scans."""

    def __init__(self, ttl_seconds: int = 5) -> None:
        """
        Initialize results cache.

        Args:
            ttl_seconds: Time-to-live for cached results (default: 5s)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[datetime, "ScanResult"]] = {}

    def get(self, symbol: str) -> "ScanResult | None":
        """Get cached result if not expired."""
        entry = self._cache.get(symbol.upper())
        if entry is None:
            return None

        cached_at, result = entry
        if datetime.now(timezone.utc) - cached_at > timedelta(seconds=self.ttl_seconds):
            del self._cache[symbol.upper()]
            return None

        return result

    def put(self, result: "ScanResult") -> None:
        """Cache a scan result."""
        self._cache[result.symbol.upper()] = (datetime.now(timezone.utc), result)

    def invalidate(self, symbol: str) -> None:
        """Remove symbol from cache."""
        self._cache.pop(symbol.upper(), None)

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
