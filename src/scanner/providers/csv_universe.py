"""
CSV-based universe provider for v1 testing.
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CSVUniverseProvider:
    """Static CSV list – v1 implementation for testing."""

    def __init__(self, csv_path: str | Path) -> None:
        """
        Initialize with path to universe CSV.

        Args:
            csv_path: Path to CSV file with 'symbol' column
        """
        self.csv_path = Path(csv_path)
        self._universe: list[str] = []
        self.refresh()

    def get_universe(self) -> list[str]:
        """Return list of symbols to scan."""
        return self._universe

    def refresh(self) -> None:
        """Reload universe from CSV file."""
        if not self.csv_path.exists():
            logger.warning(f"Universe CSV not found: {self.csv_path}")
            self._universe = []
            return

        df = pd.read_csv(self.csv_path)

        if "symbol" not in df.columns:
            logger.error(f"Universe CSV missing 'symbol' column: {self.csv_path}")
            self._universe = []
            return

        self._universe = df["symbol"].dropna().str.upper().tolist()
        logger.info(f"Loaded {len(self._universe)} symbols from {self.csv_path}")
