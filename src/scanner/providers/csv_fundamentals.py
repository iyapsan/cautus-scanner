"""
CSV-based fundamentals provider for v1 (float data).
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CSVFloatProvider:
    """CSV implementation for v1 float data."""

    def __init__(self, csv_path: str | Path) -> None:
        """
        Initialize with path to float data CSV.

        Args:
            csv_path: Path to CSV with 'symbol' and 'float_shares' columns
        """
        self.csv_path = Path(csv_path)
        self._data: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        """Load float data from CSV."""
        if not self.csv_path.exists():
            logger.warning(f"Float data CSV not found: {self.csv_path}")
            return

        df = pd.read_csv(self.csv_path)

        required_cols = {"symbol", "float_shares"}
        if not required_cols.issubset(df.columns):
            logger.error(f"Float CSV missing required columns: {required_cols}")
            return

        for _, row in df.iterrows():
            symbol = str(row["symbol"]).upper()
            float_shares = row["float_shares"]
            if pd.notna(float_shares):
                self._data[symbol] = int(float_shares)

        logger.info(f"Loaded float data for {len(self._data)} symbols")

    def get_float_shares(self, symbol: str) -> int | None:
        """Get float shares for a symbol."""
        return self._data.get(symbol.upper())
