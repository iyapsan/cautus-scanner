"""
Mock Market Data Provider for testing without IBKR connection.
"""

import random
from datetime import datetime


class MockMarketDataProvider:
    """
    In-memory mock provider for unit tests.
    
    Generates realistic-looking dummy data.
    """

    def __init__(self, data: dict | None = None) -> None:
        """
        Initialize with optional preset data.

        Args:
            data: Dict of symbol -> {price, prev_close, volume, historical}
        """
        self._data = data or {}
        self._default_volume = 1_000_000

    def set_data(self, symbol: str, **kwargs) -> None:
        """Set mock data for a symbol."""
        self._data[symbol.upper()] = kwargs

    def get_last_price(self, symbol: str) -> float:
        """Get mocked price."""
        data = self._data.get(symbol.upper(), {})
        if "price" in data:
            return data["price"]
        # Generate random price between $5-$50
        return round(random.uniform(5.0, 50.0), 2)

    def get_prev_close(self, symbol: str) -> float:
        """Get mocked previous close."""
        data = self._data.get(symbol.upper(), {})
        if "prev_close" in data:
            return data["prev_close"]
        # Slightly different from current price
        price = self.get_last_price(symbol)
        return round(price * random.uniform(0.9, 1.1), 2)

    def get_intraday_volume(self, symbol: str) -> int:
        """Get mocked intraday volume."""
        data = self._data.get(symbol.upper(), {})
        if "volume" in data:
            return data["volume"]
        return int(self._default_volume * random.uniform(0.5, 5.0))

    def get_historical_daily_volume(self, symbol: str, lookback_days: int = 30) -> list[int]:
        """Get mocked historical volumes."""
        data = self._data.get(symbol.upper(), {})
        if "historical" in data:
            return data["historical"]
        
        avg = self._default_volume
        return [int(avg * random.uniform(0.7, 1.3)) for _ in range(lookback_days)]
