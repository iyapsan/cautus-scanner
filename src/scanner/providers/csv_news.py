"""
CSV-based news/catalyst provider for v1.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from scanner.models import Catalyst

logger = logging.getLogger(__name__)


class CSVCatalystProvider:
    """CSV implementation for v1 catalyst data."""

    def __init__(self, csv_path: str | Path) -> None:
        """
        Initialize with path to catalyst CSV.

        Args:
            csv_path: Path to CSV with symbol, headline, catalyst_type, timestamp columns
        """
        self.csv_path = Path(csv_path)
        self._data: dict[str, list[Catalyst]] = {}
        self._load()

    def _load(self) -> None:
        """Load catalyst data from CSV."""
        if not self.csv_path.exists():
            logger.warning(f"Catalyst CSV not found: {self.csv_path}")
            return

        df = pd.read_csv(self.csv_path)

        required_cols = {"symbol", "headline", "catalyst_type", "timestamp"}
        if not required_cols.issubset(df.columns):
            logger.error(f"Catalyst CSV missing required columns: {required_cols}")
            return

        for _, row in df.iterrows():
            symbol = str(row["symbol"]).upper()
            catalyst = Catalyst(
                symbol=symbol,
                headline=str(row["headline"]),
                catalyst_type=str(row["catalyst_type"]).lower(),
                timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                source="csv",
            )

            if symbol not in self._data:
                self._data[symbol] = []
            self._data[symbol].append(catalyst)

        logger.info(f"Loaded catalysts for {len(self._data)} symbols")

    def get_recent_catalyst(self, symbol: str, lookback_hours: int = 24) -> Catalyst | None:
        """
        Get most recent catalyst for a symbol within lookback window.

        Args:
            symbol: Stock symbol
            lookback_hours: Hours to look back for catalyst

        Returns:
            Most recent Catalyst or None if none found
        """
        catalysts = self._data.get(symbol.upper(), [])
        if not catalysts:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        # Find most recent catalyst within lookback
        recent = [c for c in catalysts if c.timestamp.replace(tzinfo=timezone.utc) >= cutoff]

        if not recent:
            return None

        # Return most recent
        return max(recent, key=lambda c: c.timestamp)
