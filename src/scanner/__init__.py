"""
Cautus Scanner - Low-latency momentum stock scanner.

Usage:
    from scanner import ScannerModule
    
    scanner = ScannerModule.from_config("scanner.yaml")
    results = scanner.scan()
"""

from scanner.module import ScannerModule
from scanner.models import ScanResult, PillarResult, ProviderBundle

__all__ = [
    "ScannerModule",
    "ScanResult",
    "PillarResult",
    "ProviderBundle",
]

__version__ = "0.1.0"
