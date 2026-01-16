"""
Momentum Pillar - Evaluates displacement + participation + timing.

Uses EARLY-SESSION relative volume (09:30-11:00 ET window).
Velocity: % displacement per unit time within the early-session window.
Early-session RVol is normalized to elapsed session time.
"""

from typing import Any

from scanner.models import PillarResult
from scanner.pillars.base import BasePillar
from scanner.utils.time_utils import is_early_session, get_session_elapsed_minutes


class MomentumPillar(BasePillar):
    """
    Evaluates displacement + participation + timing.
    
    Key principle: "Early expansion > late explosion"
    
    Configurable parameters:
    - min_pct_move: Minimum % change from previous close (default: 10.0)
    - min_early_session_rvol: Minimum RVol in early session (default: 5.0)
    - time_window.start: Early session start (default: 09:30)
    - time_window.end: Early session end (default: 11:00)
    """

    @property
    def name(self) -> str:
        return "momentum"

    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Check momentum criteria: % move + early-session RVol + timing.

        Args:
            symbol: Stock symbol
            context: Must contain 'price', 'prev_close', 'intraday_volume', 'avg_volume'

        Returns:
            PillarResult indicating pass/fail with detailed reason
        """
        price = context.get("price")
        prev_close = context.get("prev_close")
        intraday_volume = context.get("intraday_volume")
        avg_volume = context.get("avg_volume")
        timestamp = context.get("timestamp")

        # Check required data
        if None in (price, prev_close):
            return self._fail("Price or previous close unavailable")

        if prev_close == 0:
            return self._fail("Previous close is zero")

        # Calculate % change
        pct_change = ((price - prev_close) / prev_close) * 100

        # Check % move threshold
        if abs(pct_change) < self.min_pct_move:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=pct_change,
                threshold=self.min_pct_move,
                reason=f"% change {pct_change:+.1f}% below threshold {self.min_pct_move}%",
            )

        # Check early-session RVol (velocity-aware)
        if intraday_volume is None or avg_volume is None or avg_volume == 0:
            return self._fail("Volume data unavailable for RVol calculation")

        # Normalize RVol to elapsed session time
        elapsed_minutes = get_session_elapsed_minutes(timestamp)
        if elapsed_minutes <= 0:
            elapsed_minutes = 1  # Avoid division by zero pre-market

        # Expected volume at this point in session (assuming 390 min trading day)
        session_fraction = min(elapsed_minutes / 390, 1.0)
        expected_volume = avg_volume * session_fraction
        
        if expected_volume == 0:
            expected_volume = 1  # Avoid division by zero

        early_rvol = intraday_volume / expected_volume

        # Check early-session RVol threshold
        if early_rvol < self.min_early_session_rvol:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=pct_change,
                threshold=self.min_early_session_rvol,
                reason=f"Early-session RVol {early_rvol:.1f}x below threshold {self.min_early_session_rvol}x",
            )

        # Check timing preference (early expansion preferred)
        is_early = is_early_session(timestamp)
        timing_note = "early session ✓" if is_early else "late session"

        return PillarResult(
            pillar_name=self.name,
            passed=True,
            value=pct_change,
            threshold=self.min_pct_move,
            reason=f"{pct_change:+.1f}% move, RVol {early_rvol:.1f}x, {timing_note}",
        )

    def _fail(self, reason: str) -> PillarResult:
        """Helper for failure results."""
        return PillarResult(
            pillar_name=self.name,
            passed=False,
            value=None,
            threshold=None,
            reason=reason,
        )

    @property
    def min_pct_move(self) -> float:
        return self.config.get("min_pct_move", 10.0)

    @property
    def min_early_session_rvol(self) -> float:
        return self.config.get("min_early_session_rvol", 5.0)
