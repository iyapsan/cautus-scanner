"""
Core data models for scanner results and provider bundle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


def _utc_now() -> datetime:
    """Timezone-aware UTC now for dataclass default."""
    return datetime.now(timezone.utc)


@dataclass
class PillarResult:
    """Result from a single pillar evaluation."""

    pillar_name: str
    passed: bool
    value: float | str | None
    threshold: float | str | None
    reason: str


@dataclass
class ScanResult:
    """Complete scanner result for a symbol."""

    symbol: str
    price: float
    pct_change: float
    relative_volume: float
    float_shares: int | None
    catalyst: str | None
    passed_pillars: list[str] = field(default_factory=list)
    failed_pillars: list[str] = field(default_factory=list)
    pillar_details: dict[str, PillarResult] = field(default_factory=dict)
    momentum_score: float | None = None
    timestamp: datetime = field(default_factory=_utc_now)

    @property
    def passed_all(self) -> bool:
        """True if all enabled pillars passed."""
        return len(self.failed_pillars) == 0


# Provider Protocols (defined here to avoid circular imports)


class MarketDataProvider(Protocol):
    """Powers Price, Momentum, Volume pillars."""

    def get_last_price(self, symbol: str) -> float: ...
    def get_prev_close(self, symbol: str) -> float: ...
    def get_intraday_volume(self, symbol: str) -> int: ...
    def get_historical_daily_volume(self, symbol: str, lookback_days: int) -> list[int]: ...


class NewsProvider(Protocol):
    """Powers Catalyst pillar."""

    def get_recent_catalyst(self, symbol: str, lookback_hours: int = 24) -> "Catalyst | None": ...


class FundamentalsProvider(Protocol):
    """Powers Float pillar."""

    def get_float_shares(self, symbol: str) -> int | None: ...


class UniverseProvider(Protocol):
    """Provides list of symbols to scan."""

    def get_universe(self) -> list[str]: ...
    def refresh(self) -> None: ...


@dataclass
class ProviderBundle:
    """All providers injected into scanner."""

    market_data: MarketDataProvider
    news: NewsProvider
    fundamentals: FundamentalsProvider
    universe: UniverseProvider


@dataclass
class Catalyst:
    """News/catalyst event for a symbol."""

    symbol: str
    headline: str
    catalyst_type: str  # earnings, fda, mna, contracts, guidance
    timestamp: datetime
    source: str | None = None
