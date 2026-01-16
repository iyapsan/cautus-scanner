"""
Float Pillar - Float size constraints.

Low float = higher volatility potential.
"""

from typing import Any

from scanner.models import PillarResult
from scanner.pillars.base import BasePillar


class FloatPillar(BasePillar):
    """
    Evaluates float size constraints.
    
    Configurable parameters:
    - max_shares: Maximum float shares (default: 20,000,000)
    - prefer_lower_float: Boost score for lower floats (default: true)
    """

    @property
    def name(self) -> str:
        return "float"

    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Check if float is within acceptable range.

        Args:
            symbol: Stock symbol
            context: Must contain 'float_shares' key

        Returns:
            PillarResult indicating pass/fail
        """
        float_shares = context.get("float_shares")

        # Missing float data - fail by default per PRD
        if float_shares is None:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=None,
                threshold=self._format_shares(self.max_shares),
                reason="Float data unavailable - excluded by default",
            )

        passed = float_shares <= self.max_shares

        return PillarResult(
            pillar_name=self.name,
            passed=passed,
            value=float_shares,
            threshold=self._format_shares(self.max_shares),
            reason=self._get_reason(float_shares, passed),
        )

    def _get_reason(self, float_shares: int, passed: bool) -> str:
        """Generate human-readable reason."""
        formatted = self._format_shares(float_shares)
        threshold = self._format_shares(self.max_shares)
        
        if passed:
            if float_shares < self.max_shares / 2:
                return f"Low float {formatted} (excellent) ≤ {threshold}"
            else:
                return f"Float {formatted} within limit ≤ {threshold}"
        else:
            return f"Float {formatted} exceeds maximum {threshold}"

    def _format_shares(self, shares: int) -> str:
        """Format share count for display."""
        if shares >= 1_000_000_000:
            return f"{shares / 1_000_000_000:.1f}B"
        elif shares >= 1_000_000:
            return f"{shares / 1_000_000:.1f}M"
        elif shares >= 1_000:
            return f"{shares / 1_000:.0f}K"
        else:
            return str(shares)

    @property
    def max_shares(self) -> int:
        return self.config.get("max_shares", 20_000_000)

    @property
    def prefer_lower_float(self) -> bool:
        return self.config.get("prefer_lower_float", True)
