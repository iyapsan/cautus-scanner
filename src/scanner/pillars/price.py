"""
Price Pillar - Evaluates if stock price is within configured range.
"""

from typing import Any

from scanner.models import PillarResult
from scanner.pillars.base import BasePillar


class PricePillar(BasePillar):
    """
    Evaluates if stock price falls within acceptable range.
    
    Configurable parameters:
    - min: Minimum price (default: 2.0)
    - max: Maximum price (default: 20.0)
    """

    @property
    def name(self) -> str:
        return "price"

    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Check if price is within configured range.

        Args:
            symbol: Stock symbol
            context: Must contain 'price' key with current price

        Returns:
            PillarResult indicating pass/fail
        """
        price = context.get("price")
        
        if price is None:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=None,
                threshold=f"{self.min_price}-{self.max_price}",
                reason="Price data unavailable",
            )

        passed = self.min_price <= price <= self.max_price

        return PillarResult(
            pillar_name=self.name,
            passed=passed,
            value=price,
            threshold=f"{self.min_price}-{self.max_price}",
            reason=self._get_reason(price, passed),
        )

    def _get_reason(self, price: float, passed: bool) -> str:
        """Generate human-readable reason."""
        if passed:
            return f"Price ${price:.2f} within range ${self.min_price:.2f}-${self.max_price:.2f}"
        elif price < self.min_price:
            return f"Price ${price:.2f} below minimum ${self.min_price:.2f}"
        else:
            return f"Price ${price:.2f} above maximum ${self.max_price:.2f}"

    @property
    def min_price(self) -> float:
        return self.config.get("min", 2.0)

    @property
    def max_price(self) -> float:
        return self.config.get("max", 20.0)
