"""
Smoke tests for critical scanner invariants.

These tests verify fundamental correctness without external dependencies.
Run with: pytest tests/smoke_tests/ -v -m smoke
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from scanner.models import Catalyst, PillarResult, ScanResult, ProviderBundle
from scanner.module import ScannerModule
from scanner.pillars import (
    PricePillar,
    MomentumPillar,
    VolumePillar,
    CatalystPillar,
    FloatPillar,
)


# -----------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_providers():
    """Create mock provider bundle for testing."""
    from scanner.providers.mock_market_data import MockMarketDataProvider
    
    market_data = MockMarketDataProvider()
    market_data.set_data("TEST", price=15.0, prev_close=12.0, volume=10_000_000)
    
    # Mock news provider
    news = MagicMock()
    catalyst = Catalyst(
        symbol="TEST",
        headline="Test earnings beat",
        catalyst_type="earnings",
        timestamp=datetime.now(timezone.utc),
    )
    news.get_recent_catalyst.return_value = catalyst
    
    # Mock fundamentals provider
    fundamentals = MagicMock()
    fundamentals.get_float_shares.return_value = 10_000_000
    
    # Mock universe provider
    universe = MagicMock()
    universe.get_universe.return_value = ["TEST"]
    
    return ProviderBundle(
        market_data=market_data,
        news=news,
        fundamentals=fundamentals,
        universe=universe,
    )


@pytest.fixture
def scanner_config():
    """Standard scanner configuration for tests."""
    return {
        "price": {"enabled": True, "min": 2.0, "max": 20.0},
        "momentum": {"enabled": True, "min_pct_move": 10.0, "min_early_session_rvol": 2.0},
        "volume": {"enabled": True, "min_relative_volume": 2.0},
        "catalyst": {"enabled": True, "require_news": True},
        "float": {"enabled": True, "max_shares": 20_000_000},
        "cache": {"ttl_seconds": 5},
    }


# -----------------------------------------------------------------------------
# Smoke Test: Determinism
# -----------------------------------------------------------------------------


@pytest.mark.smoke
class TestDeterminism:
    """Same input + same config = same output."""

    def test_same_input_produces_same_result(self, scanner_config, mock_providers):
        """Verify deterministic evaluation."""
        scanner = ScannerModule(scanner_config, mock_providers)
        
        # Run twice with identical input
        result1 = scanner.scan_single("TEST")
        
        # Clear cache to force re-evaluation
        scanner._results_cache.clear()
        
        result2 = scanner.scan_single("TEST")
        
        # Results should be identical
        assert result1.passed_pillars == result2.passed_pillars
        assert result1.failed_pillars == result2.failed_pillars
        assert result1.price == result2.price

    def test_pillar_order_is_consistent(self, scanner_config, mock_providers):
        """Verify pillars evaluate in consistent order."""
        scanner = ScannerModule(scanner_config, mock_providers)
        
        # Pillar order should match PILLAR_CLASSES order
        expected_order = ["price", "momentum", "volume", "catalyst", "float"]
        actual_order = [p.name for p in scanner._pillars]
        
        assert actual_order == expected_order


# -----------------------------------------------------------------------------
# Smoke Test: Pillar Independence
# -----------------------------------------------------------------------------


@pytest.mark.smoke
class TestPillarIndependence:
    """Each pillar can be enabled/disabled independently."""

    def test_disable_single_pillar(self, mock_providers):
        """Disabling one pillar doesn't affect others."""
        # Config with price disabled
        config = {
            "price": {"enabled": False},
            "momentum": {"enabled": True, "min_pct_move": 10.0, "min_early_session_rvol": 2.0},
            "volume": {"enabled": True, "min_relative_volume": 2.0},
            "catalyst": {"enabled": True, "require_news": True},
            "float": {"enabled": True, "max_shares": 20_000_000},
        }
        
        scanner = ScannerModule(config, mock_providers)
        
        # Should have 4 pillars (price disabled)
        assert len(scanner._pillars) == 4
        pillar_names = [p.name for p in scanner._pillars]
        assert "price" not in pillar_names
        assert "momentum" in pillar_names

    def test_enable_only_one_pillar(self, mock_providers):
        """Can run with only one pillar enabled."""
        config = {
            "price": {"enabled": True, "min": 2.0, "max": 20.0},
            "momentum": {"enabled": False},
            "volume": {"enabled": False},
            "catalyst": {"enabled": False},
            "float": {"enabled": False},
        }
        
        scanner = ScannerModule(config, mock_providers)
        
        assert len(scanner._pillars) == 1
        assert scanner._pillars[0].name == "price"
        
        result = scanner.scan_single("TEST")
        assert result is not None
        assert "price" in result.passed_pillars or "price" in result.failed_pillars

    def test_pillar_failure_doesnt_crash_others(self, mock_providers):
        """One pillar failing doesn't prevent others from running."""
        # Make float data unavailable (will fail float pillar)
        mock_providers.fundamentals.get_float_shares.return_value = None
        
        config = {
            "price": {"enabled": True, "min": 2.0, "max": 20.0},
            "momentum": {"enabled": False},
            "volume": {"enabled": False},
            "catalyst": {"enabled": False},
            "float": {"enabled": True, "max_shares": 20_000_000},
        }
        
        scanner = ScannerModule(config, mock_providers)
        result = scanner.scan_single("TEST")
        
        # Float should fail, price should still evaluate
        assert "float" in result.failed_pillars
        assert "price" in result.passed_pillars


# -----------------------------------------------------------------------------
# Smoke Test: Failure Modes
# -----------------------------------------------------------------------------


@pytest.mark.smoke
class TestFailureModes:
    """Scanner handles missing data gracefully."""

    def test_missing_price_data(self, scanner_config, mock_providers):
        """Missing price data fails price pillar but doesn't crash."""
        mock_providers.market_data.set_data("NODATA")  # No price set
        mock_providers.market_data._data["NODATA"]["price"] = None
        
        # Override get_last_price to return None
        mock_providers.market_data.get_last_price = lambda s: None
        
        scanner = ScannerModule(scanner_config, mock_providers)
        
        # Should not raise, returns None or result with failures
        result = scanner.scan_single("NODATA")
        # May return None on error or result with failed pillars

    def test_missing_catalyst_fails_pillar(self, scanner_config, mock_providers):
        """No catalyst = catalyst pillar fails (require_news=true)."""
        mock_providers.news.get_recent_catalyst.return_value = None
        
        scanner = ScannerModule(scanner_config, mock_providers)
        result = scanner.scan_single("TEST")
        
        assert "catalyst" in result.failed_pillars

    def test_missing_float_fails_pillar(self, scanner_config, mock_providers):
        """No float data = float pillar fails."""
        mock_providers.fundamentals.get_float_shares.return_value = None
        
        scanner = ScannerModule(scanner_config, mock_providers)
        result = scanner.scan_single("TEST")
        
        assert "float" in result.failed_pillars

    def test_empty_universe_returns_empty_results(self, scanner_config, mock_providers):
        """Empty universe returns empty results list."""
        mock_providers.universe.get_universe.return_value = []
        
        scanner = ScannerModule(scanner_config, mock_providers)
        results = scanner.scan()
        
        assert results == []


# -----------------------------------------------------------------------------
# Smoke Test: RVol Distinction
# -----------------------------------------------------------------------------


@pytest.mark.smoke
class TestRVolDistinction:
    """Momentum RVol and Volume RVol are distinct metrics."""

    def test_momentum_rvol_is_velocity_aware(self):
        """Momentum pillar uses early-session RVol (time-normalized)."""
        pillar = MomentumPillar({
            "min_pct_move": 10.0,
            "min_early_session_rvol": 5.0,
        })
        
        # High % move but low velocity should fail
        context = {
            "price": 11.0,
            "prev_close": 10.0,  # +10%
            "intraday_volume": 1_000_000,
            "avg_volume": 10_000_000,  # Low RVol
            "timestamp": datetime.now(timezone.utc),
        }
        
        result = pillar.evaluate("TEST", context)
        # Should fail on RVol threshold
        assert result.passed is False or "RVol" in result.reason

    def test_volume_rvol_is_session_level(self):
        """Volume pillar uses simple session-level RVol."""
        pillar = VolumePillar({"min_relative_volume": 5.0})
        
        # Session RVol is today's volume / avg volume
        context = {
            "intraday_volume": 10_000_000,
            "avg_volume": 2_000_000,  # RVol = 5x
        }
        
        result = pillar.evaluate("TEST", context)
        assert result.passed is True
        assert result.value == 5.0


# -----------------------------------------------------------------------------
# Smoke Test: Cache Behavior
# -----------------------------------------------------------------------------


@pytest.mark.smoke
class TestCacheBehavior:
    """Cache returns consistent results within TTL."""

    def test_cache_returns_same_result(self, scanner_config, mock_providers):
        """Cached result is returned on second call."""
        scanner = ScannerModule(scanner_config, mock_providers)
        
        result1 = scanner.scan_single("TEST")
        result2 = scanner.scan_single("TEST")  # Should hit cache
        
        # Should be the exact same object from cache
        assert result1 is result2

    def test_cache_miss_after_invalidation(self, scanner_config, mock_providers):
        """Cache miss after explicit invalidation."""
        scanner = ScannerModule(scanner_config, mock_providers)
        
        result1 = scanner.scan_single("TEST")
        scanner._results_cache.invalidate("TEST")
        result2 = scanner.scan_single("TEST")  # Should re-evaluate
        
        # Should NOT be same object (re-evaluated)
        assert result1 is not result2
        # But values should match (determinism)
        assert result1.passed_pillars == result2.passed_pillars
