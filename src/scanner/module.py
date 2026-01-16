"""
ScannerModule - Main orchestrator for pillar-based stock scanning.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from scanner.engine.cache import HistoricalDataCache, ScannerResultsCache
from scanner.models import PillarResult, ProviderBundle, ScanResult
from scanner.pillars.base import BasePillar
from scanner.pillars.catalyst import CatalystPillar
from scanner.pillars.float_size import FloatPillar
from scanner.pillars.momentum import MomentumPillar
from scanner.pillars.price import PricePillar
from scanner.pillars.volume import VolumePillar

logger = logging.getLogger(__name__)


class ScannerModule:
    """
    Real-time momentum stock scanner with configurable pillar evaluation.

    Usage:
        scanner = ScannerModule.from_config("scanner.yaml")
        results = scanner.scan()
        for result in results:
            if result.passed_all:
                print(f"{result.symbol}: {result.passed_pillars}")
    """

    # Pillar registry - order matters for evaluation
    PILLAR_CLASSES: dict[str, type[BasePillar]] = {
        "price": PricePillar,
        "momentum": MomentumPillar,
        "volume": VolumePillar,
        "catalyst": CatalystPillar,
        "float": FloatPillar,
    }

    def __init__(self, config: dict, providers: ProviderBundle) -> None:
        """
        Initialize scanner with config and providers.

        Args:
            config: Scanner configuration dict
            providers: Bundle of all data providers
        """
        self.config = config
        self.providers = providers
        self._pillars: list[BasePillar] = []
        self._historical_cache = HistoricalDataCache()
        self._results_cache = ScannerResultsCache(
            ttl_seconds=config.get("cache", {}).get("ttl_seconds", 5)
        )
        self._init_pillars()
        logger.info(f"ScannerModule initialized with {len(self._pillars)} pillars")

    def _init_pillars(self) -> None:
        """Initialize pillar evaluators from config."""
        for name, pillar_cls in self.PILLAR_CLASSES.items():
            pillar_config = self.config.get(name, {})
            
            # Skip disabled pillars
            if not pillar_config.get("enabled", True):
                logger.info(f"Pillar '{name}' is disabled")
                continue

            pillar = pillar_cls(pillar_config)
            self._pillars.append(pillar)
            logger.debug(f"Initialized pillar: {name}")

    @classmethod
    def from_config(cls, config_file: str = "scanner.yaml") -> "ScannerModule":
        """
        Create ScannerModule from YAML configuration file.

        Args:
            config_file: Path to YAML config file

        Returns:
            Initialized ScannerModule instance
        """
        from scanner.config import load_config
        from scanner.providers.factory import ProviderFactory

        config = load_config(Path(config_file))
        providers = ProviderFactory.create_bundle(config.get("providers", {}))

        return cls(config.get("scanner", {}), providers)

    def warm_cache(self) -> None:
        """
        Pre-market cache warming. Call before market open.
        
        Fetches 30-day avg volume for all symbols in universe.
        """
        symbols = self.providers.universe.get_universe()
        self._historical_cache.warm(symbols, self.providers.market_data)

    def scan(self) -> list[ScanResult]:
        """
        Scan entire universe and return qualifying results.

        Returns:
            List of ScanResult for all evaluated symbols
        """
        universe = self.providers.universe.get_universe()
        results = []

        for symbol in universe:
            result = self.scan_single(symbol)
            if result is not None:
                results.append(result)

        logger.info(f"Scan complete: {len(results)} results from {len(universe)} symbols")
        return results

    def scan_single(self, symbol: str) -> ScanResult | None:
        """
        Evaluate a single symbol against all pillars.

        Args:
            symbol: Stock symbol to evaluate

        Returns:
            ScanResult if symbol was evaluated, None on error
        """
        # Check results cache first
        cached = self._results_cache.get(symbol)
        if cached is not None:
            return cached

        try:
            # Build evaluation context
            context = self._build_context(symbol)
            
            # Evaluate all enabled pillars
            passed_pillars: list[str] = []
            failed_pillars: list[str] = []
            pillar_details: dict[str, PillarResult] = {}

            for pillar in self._pillars:
                result = pillar.evaluate(symbol, context)
                pillar_details[pillar.name] = result
                
                if result.passed:
                    passed_pillars.append(pillar.name)
                else:
                    failed_pillars.append(pillar.name)

            # Build scan result
            scan_result = ScanResult(
                symbol=symbol,
                price=context.get("price", 0.0),
                pct_change=self._calc_pct_change(context),
                relative_volume=self._calc_rvol(context),
                float_shares=context.get("float_shares"),
                catalyst=context.get("catalyst").headline if context.get("catalyst") else None,
                passed_pillars=passed_pillars,
                failed_pillars=failed_pillars,
                pillar_details=pillar_details,
            )

            # Cache result
            self._results_cache.put(scan_result)

            return scan_result

        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None

    def _build_context(self, symbol: str) -> dict[str, Any]:
        """
        Build evaluation context for a symbol by fetching all required data.

        Args:
            symbol: Stock symbol

        Returns:
            Context dict with all data needed by pillars
        """
        md = self.providers.market_data
        
        # Get price data
        price = md.get_last_price(symbol)
        prev_close = md.get_prev_close(symbol)
        
        # Get volume data
        intraday_volume = md.get_intraday_volume(symbol)
        
        # Use cached avg or fetch
        avg_volume = self._historical_cache.get_avg_volume(symbol)
        if avg_volume is None:
            # Fallback: compute on-the-fly (slower)
            historical = md.get_historical_daily_volume(symbol, lookback_days=30)
            avg_volume = sum(historical) / len(historical) if historical else 0

        # Get catalyst
        catalyst = self.providers.news.get_recent_catalyst(symbol, lookback_hours=24)

        # Get float
        float_shares = self.providers.fundamentals.get_float_shares(symbol)

        return {
            "price": price,
            "prev_close": prev_close,
            "intraday_volume": intraday_volume,
            "avg_volume": avg_volume,
            "catalyst": catalyst,
            "float_shares": float_shares,
            "timestamp": datetime.now(),
        }

    def _calc_pct_change(self, context: dict[str, Any]) -> float:
        """Calculate % change from context."""
        price = context.get("price", 0)
        prev = context.get("prev_close", 0)
        if prev == 0:
            return 0.0
        return ((price - prev) / prev) * 100

    def _calc_rvol(self, context: dict[str, Any]) -> float:
        """Calculate relative volume from context."""
        vol = context.get("intraday_volume", 0)
        avg = context.get("avg_volume", 0)
        if avg == 0:
            return 0.0
        return vol / avg
