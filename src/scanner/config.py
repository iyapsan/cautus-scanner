"""
Configuration loader and validation.
"""

import logging
import os
from pathlib import Path

import yaml

from scanner.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


# =============================================================================
# CENTRALIZED DEFAULTS
# =============================================================================
# All default values in one place. Import and use these in providers/factory.

DEFAULTS = {
    # IBKR connection
    "ibkr": {
        "host": "127.0.0.1",
        "port": 7497,  # TWS default (4002 for Gateway)
        "client_id": 1,
        "timeout": 10,
        "market_data_type": 1,  # 1=live, 3=delayed
    },
    
    # IBKR Universe Scanner
    "universe": {
        "provider": "csv",
        "csv_path": "data/universe.csv",
        "port": 4002,
        "client_id": 2,  # Different from market data
        "price_min": 2.0,
        "price_max": 20.0,
        "volume_min": 500_000,
        "percent_change_min": 5.0,
        "max_results": 50,
    },
    
    # Pillars
    "price": {
        "enabled": True,
        "min": 2.0,
        "max": 20.0,
    },
    "momentum": {
        "enabled": True,
        "min_pct_move": 10.0,
        "min_early_session_rvol": 5.0,
    },
    "volume": {
        "enabled": True,
        "min_relative_volume": 5.0,
        "lookback_days": 30,
    },
    "catalyst": {
        "enabled": True,
        "require_news": True,
        "lookback_hours": 24,
    },
    "float": {
        "enabled": True,
        "max_shares": 20_000_000,
    },
    
    # Cache
    "cache": {
        "ttl_seconds": 5,
    },
}


def load_config(config_path: Path) -> dict:
    """
    Load and validate scanner configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigurationError: If config file not found or invalid
    """
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ConfigurationError(f"Empty configuration file: {config_path}")

    # Expand environment variables
    config = _expand_env_vars(config)

    # Validate required sections
    _validate_config(config)

    logger.info(f"Loaded configuration from {config_path}")
    return config


def _expand_env_vars(obj: dict | list | str) -> dict | list | str:
    """Recursively expand ${VAR} patterns in config values."""
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        value = os.environ.get(var_name)
        if value is None:
            logger.warning(f"Environment variable not set: {var_name}")
            return obj
        return value
    return obj


def _validate_config(config: dict) -> None:
    """Validate configuration structure."""
    if "providers" not in config:
        raise ConfigurationError("Missing required 'providers' section in config")

    providers = config["providers"]
    required_providers = ["market_data", "news", "fundamentals"]

    for provider in required_providers:
        if provider not in providers:
            raise ConfigurationError(f"Missing required provider: {provider}")
        if "type" not in providers[provider]:
            raise ConfigurationError(f"Missing 'type' in provider: {provider}")
