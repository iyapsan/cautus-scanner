"""
Configuration loader and validation.
"""

import logging
import os
from pathlib import Path

import yaml

from scanner.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


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
