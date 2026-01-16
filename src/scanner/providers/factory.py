"""
ProviderFactory - Config-driven provider instantiation.
"""

import logging

from scanner.config import DEFAULTS
from scanner.exceptions import ConfigurationError
from scanner.models import (
    FundamentalsProvider,
    MarketDataProvider,
    NewsProvider,
    ProviderBundle,
    UniverseProvider,
)

logger = logging.getLogger(__name__)


def _get(config: dict, key: str, section: str) -> any:
    """Get config value with centralized default fallback."""
    return config.get(key, DEFAULTS.get(section, {}).get(key))


class ProviderFactory:
    """Config-driven provider instantiation."""

    @staticmethod
    def create_market_data(config: dict) -> MarketDataProvider:
        """Create market data provider from config."""
        provider_type = config.get("type")

        if provider_type == "ibkr":
            from scanner.providers.ibkr_market_data import IBKRMarketDataProvider

            return IBKRMarketDataProvider(
                host=_get(config, "host", "ibkr"),
                port=_get(config, "port", "ibkr"),
                client_id=_get(config, "client_id", "ibkr"),
                market_data_type=_get(config, "market_data_type", "ibkr"),
            )
        else:
            raise ConfigurationError(f"Unknown market_data provider type: {provider_type}")

    @staticmethod
    def create_news(config: dict) -> NewsProvider:
        """Create news provider from config."""
        provider_type = config.get("type")

        if provider_type == "csv":
            from scanner.providers.csv_news import CSVCatalystProvider

            return CSVCatalystProvider(csv_path=config.get("csv_path"))
        else:
            raise ConfigurationError(f"Unknown news provider type: {provider_type}")

    @staticmethod
    def create_fundamentals(config: dict) -> FundamentalsProvider:
        """Create fundamentals provider from config."""
        provider_type = config.get("type")

        if provider_type == "csv":
            from scanner.providers.csv_fundamentals import CSVFloatProvider

            return CSVFloatProvider(csv_path=config.get("csv_path"))
        else:
            raise ConfigurationError(f"Unknown fundamentals provider type: {provider_type}")

    @staticmethod
    def create_universe(config: dict) -> UniverseProvider:
        """Create universe provider from config."""
        provider_type = _get(config, "provider", "universe")

        if provider_type == "csv":
            from scanner.providers.csv_universe import CSVUniverseProvider

            return CSVUniverseProvider(csv_path=_get(config, "csv_path", "universe"))
        
        elif provider_type == "ibkr":
            from scanner.providers.ibkr_universe import IBKRUniverseProvider

            return IBKRUniverseProvider(
                host=_get(config, "host", "ibkr"),
                port=_get(config, "port", "universe"),
                client_id=_get(config, "client_id", "universe"),
                market_data_type=_get(config, "market_data_type", "ibkr"),
                price_min=_get(config, "price_min", "universe"),
                price_max=_get(config, "price_max", "universe"),
                volume_min=_get(config, "volume_min", "universe"),
                percent_change_min=_get(config, "percent_change_min", "universe"),
                max_results=_get(config, "max_results", "universe"),
            )
        else:
            raise ConfigurationError(f"Unknown universe provider type: {provider_type}")

    @classmethod
    def create_bundle(cls, config: dict) -> ProviderBundle:
        """Create complete provider bundle from config."""
        logger.info("Creating provider bundle from config")

        return ProviderBundle(
            market_data=cls.create_market_data(config.get("market_data", {})),
            news=cls.create_news(config.get("news", {})),
            fundamentals=cls.create_fundamentals(config.get("fundamentals", {})),
            universe=cls.create_universe(config.get("universe", {})),
        )
