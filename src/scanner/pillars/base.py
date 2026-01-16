"""
Base pillar interface for all scanner pillars.
"""

from abc import ABC, abstractmethod
from typing import Any

from scanner.models import PillarResult


class BasePillar(ABC):
    """Abstract base class for scanner pillars."""

    def __init__(self, config: dict) -> None:
        """
        Initialize pillar with configuration.

        Args:
            config: Pillar-specific configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Pillar identifier (e.g., 'price', 'momentum')."""
        ...

    @abstractmethod
    def evaluate(self, symbol: str, context: dict[str, Any]) -> PillarResult:
        """
        Evaluate this pillar for a given symbol.

        Args:
            symbol: Stock symbol to evaluate
            context: Evaluation context with provider data

        Returns:
            PillarResult with pass/fail and explanation
        """
        ...
