"""
Catalyst Pillar - Hard-gated news/catalyst verification.

"No real news = no continuation"

This pillar is MANDATORY in v1 (require_news: true is non-optional).
"""

from typing import Any

from scanner.models import Catalyst, PillarResult
from scanner.pillars.base import BasePillar


# Valid catalyst types
ALLOWED_CATALYST_TYPES = {"earnings", "fda", "mna", "contracts", "guidance"}

# Explicitly excluded - these are NOT valid catalysts
EXCLUDED_TYPES = {"rumor", "sympathy", "social", "technical"}


class CatalystPillar(BasePillar):
    """
    Hard-gated news/catalyst verification.
    
    Key principle: "No real news = no continuation"
    
    Configurable parameters:
    - require_news: Must have catalyst to pass (default: true, mandatory in v1)
    - allowed_types: List of valid catalyst types
    """

    @property
    def name(self) -> str:
        return "catalyst"

    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Verify symbol has a valid, real catalyst.

        Args:
            symbol: Stock symbol
            context: Must contain 'catalyst' key with Catalyst object or None

        Returns:
            PillarResult indicating pass/fail
        """
        catalyst: Catalyst | None = context.get("catalyst")

        # No catalyst found
        if catalyst is None:
            if self.require_news:
                return PillarResult(
                    pillar_name=self.name,
                    passed=False,
                    value=None,
                    threshold="requires news",
                    reason="No catalyst found - rejected (require_news=true)",
                )
            else:
                # This branch shouldn't execute in v1 (require_news is mandatory)
                return PillarResult(
                    pillar_name=self.name,
                    passed=True,
                    value=None,
                    threshold=None,
                    reason="No catalyst, but require_news=false",
                )

        # Validate catalyst type
        catalyst_type = catalyst.catalyst_type.lower()

        # Check if explicitly excluded
        if catalyst_type in EXCLUDED_TYPES:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=catalyst_type,
                threshold=str(self.allowed_types),
                reason=f"Catalyst type '{catalyst_type}' is explicitly excluded",
            )

        # Check if in allowed list
        if catalyst_type not in self.allowed_types:
            return PillarResult(
                pillar_name=self.name,
                passed=False,
                value=catalyst_type,
                threshold=str(self.allowed_types),
                reason=f"Catalyst type '{catalyst_type}' not in allowed list",
            )

        # Valid catalyst
        return PillarResult(
            pillar_name=self.name,
            passed=True,
            value=catalyst_type,
            threshold=str(self.allowed_types),
            reason=f"Valid catalyst: {catalyst_type} - {catalyst.headline[:50]}...",
        )

    @property
    def require_news(self) -> bool:
        # Mandatory in v1 - always returns True
        return self.config.get("require_news", True)

    @property
    def allowed_types(self) -> set[str]:
        configured = self.config.get("allowed_types", list(ALLOWED_CATALYST_TYPES))
        return {t.lower() for t in configured}
