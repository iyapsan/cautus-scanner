"""
ProviderFactory - Config-driven provider instantiation.
"""

import logging

from scanner.exceptions import ConfigurationError
from scanner.models import (
    FundamentalsProvider,
    MarketDataProvider,
    NewsProvider,
    ProviderBundle,
    UniverseProvider,
)

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Config-driven provider instantiation."""

    @staticmethod
    def create_market_data(config: dict) -> MarketDataProvider:
        """Create market data provider from config."""
        provider_type = config.get("type")

        if provider_type == "ibkr":
            from scanner.providers.ibkr_market_data import IBKRMarketDataProvider

            return IBKRMarketDataProvider(
                host=config.get("host", "127.0.0.1"),
                port=config.get("port", 7497),
                client_id=config.get("client_id", 1),
                market_data_type=config.get("market_data_type", 1),  # 1=live (default), 3=delayed
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
        provider_type = config.get("provider", "csv")

        if provider_type == "csv":
            from scanner.providers.csv_universe import CSVUniverseProvider

            return CSVUniverseProvider(csv_path=config.get("csv_path", "data/universe.csv"))
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
