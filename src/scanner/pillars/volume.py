"""
Volume Pillar - Session-level relative volume confirmation.

Uses FULL-SESSION relative volume (today vs 30-day avg).
Independent from Momentum pillar's early-session velocity check.
"""

from typing import Any

from scanner.models import PillarResult
from scanner.pillars.base import BasePillar


class VolumePillar(BasePillar):
    """
    Session-level volume confirmation.
    
    Configurable parameters:
    - min_relative_volume: Minimum RVol vs 30-day avg (default: 5.0)
    - lookback_days: Days for average calculation (default: 30)
    """

    @property
    def name(self) -> str:
        return "volume"

    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Check session-level relative volume.

        Args:
            symbol: Stock symbol
            context: Must contain 'intraday_volume', 'avg_volume'

        Returns:
            PillarResult indicating pass/fail
        """
        intraday_volume = context.get("intraday_volume")
        avg_volume = context.get("avg_volume")

        if intraday_volume is None:
            return self._fail("Intraday volume unavailable")

        if avg_volume is None or avg_volume == 0:
            return self._fail("Average volume unavailable")

        # Calculate relative volume
        rvol = intraday_volume / avg_volume

        passed = rvol >= self.min_relative_volume

        return PillarResult(
            pillar_name=self.name,
            passed=passed,
            value=rvol,
            threshold=self.min_relative_volume,
            reason=self._get_reason(rvol, passed),
        )

    def _fail(self, reason: str) -> PillarResult:
        """Helper for failure results."""
        return PillarResult(
            pillar_name=self.name,
            passed=False,
            value=None,
            threshold=self.min_relative_volume,
            reason=reason,
        )

    def _get_reason(self, rvol: float, passed: bool) -> str:
        """Generate human-readable reason."""
        if passed:
            return f"RVol {rvol:.1f}x meets threshold {self.min_relative_volume}x"
        else:
            return f"RVol {rvol:.1f}x below threshold {self.min_relative_volume}x"

    @property
    def min_relative_volume(self) -> float:
        return self.config.get("min_relative_volume", 5.0)

    @property
    def lookback_days(self) -> int:
        return self.config.get("lookback_days", 30)
