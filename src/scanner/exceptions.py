"""
Custom exceptions for scanner module.
"""


class ScannerError(Exception):
    """Base exception for scanner errors."""

    pass


class ConfigurationError(ScannerError):
    """Invalid or missing configuration."""

    pass


class ProviderError(ScannerError):
    """Error from data provider."""

    pass


class PillarEvaluationError(ScannerError):
    """Error during pillar evaluation."""

    pass
