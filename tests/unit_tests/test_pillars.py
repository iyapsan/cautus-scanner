"""
Unit tests for pillar evaluators.
"""

import pytest
from datetime import datetime, timezone

from scanner.pillars import (
    PricePillar,
    MomentumPillar,
    VolumePillar,
    CatalystPillar,
    FloatPillar,
)
from scanner.models import Catalyst


class TestPricePillar:
    """Tests for PricePillar."""

    def test_price_within_range_passes(self):
        pillar = PricePillar({"min": 2.0, "max": 20.0})
        result = pillar.evaluate("TEST", {"price": 10.0})
        assert result.passed is True
        assert result.value == 10.0

    def test_price_below_min_fails(self):
        pillar = PricePillar({"min": 2.0, "max": 20.0})
        result = pillar.evaluate("TEST", {"price": 1.50})
        assert result.passed is False
        assert "below minimum" in result.reason

    def test_price_above_max_fails(self):
        pillar = PricePillar({"min": 2.0, "max": 20.0})
        result = pillar.evaluate("TEST", {"price": 25.0})
        assert result.passed is False
        assert "above maximum" in result.reason

    def test_price_at_boundaries_passes(self):
        pillar = PricePillar({"min": 2.0, "max": 20.0})
        assert pillar.evaluate("TEST", {"price": 2.0}).passed is True
        assert pillar.evaluate("TEST", {"price": 20.0}).passed is True

    def test_missing_price_fails(self):
        pillar = PricePillar({"min": 2.0, "max": 20.0})
        result = pillar.evaluate("TEST", {})
        assert result.passed is False
        assert "unavailable" in result.reason


class TestVolumePillar:
    """Tests for VolumePillar (session-level RVol)."""

    def test_high_rvol_passes(self):
        pillar = VolumePillar({"min_relative_volume": 5.0})
        result = pillar.evaluate("TEST", {
            "intraday_volume": 10_000_000,
            "avg_volume": 1_000_000,  # RVol = 10x
        })
        assert result.passed is True
        assert result.value == 10.0

    def test_low_rvol_fails(self):
        pillar = VolumePillar({"min_relative_volume": 5.0})
        result = pillar.evaluate("TEST", {
            "intraday_volume": 2_000_000,
            "avg_volume": 1_000_000,  # RVol = 2x
        })
        assert result.passed is False
        assert "below threshold" in result.reason

    def test_missing_volume_fails(self):
        pillar = VolumePillar({"min_relative_volume": 5.0})
        result = pillar.evaluate("TEST", {"avg_volume": 1_000_000})
        assert result.passed is False

    def test_zero_avg_volume_fails(self):
        pillar = VolumePillar({"min_relative_volume": 5.0})
        result = pillar.evaluate("TEST", {
            "intraday_volume": 1_000_000,
            "avg_volume": 0,
        })
        assert result.passed is False


class TestCatalystPillar:
    """Tests for CatalystPillar (hard-gated news)."""

    def test_valid_catalyst_passes(self):
        pillar = CatalystPillar({"require_news": True, "allowed_types": ["earnings", "fda"]})
        catalyst = Catalyst(
            symbol="TEST",
            headline="Company reports Q4 earnings beat",
            catalyst_type="earnings",
            timestamp=datetime.now(timezone.utc),
        )
        result = pillar.evaluate("TEST", {"catalyst": catalyst})
        assert result.passed is True
        assert "Valid catalyst" in result.reason

    def test_no_catalyst_fails_when_required(self):
        pillar = CatalystPillar({"require_news": True})
        result = pillar.evaluate("TEST", {"catalyst": None})
        assert result.passed is False
        assert "No catalyst" in result.reason

    def test_excluded_type_fails(self):
        pillar = CatalystPillar({"require_news": True})
        catalyst = Catalyst(
            symbol="TEST",
            headline="Social media rumor",
            catalyst_type="rumor",  # Explicitly excluded
            timestamp=datetime.now(timezone.utc),
        )
        result = pillar.evaluate("TEST", {"catalyst": catalyst})
        assert result.passed is False
        assert "excluded" in result.reason

    def test_invalid_type_fails(self):
        pillar = CatalystPillar({"require_news": True, "allowed_types": ["earnings"]})
        catalyst = Catalyst(
            symbol="TEST",
            headline="Random news",
            catalyst_type="unknown_type",
            timestamp=datetime.now(timezone.utc),
        )
        result = pillar.evaluate("TEST", {"catalyst": catalyst})
        assert result.passed is False
        assert "not in allowed list" in result.reason


class TestFloatPillar:
    """Tests for FloatPillar."""

    def test_low_float_passes(self):
        pillar = FloatPillar({"max_shares": 20_000_000})
        result = pillar.evaluate("TEST", {"float_shares": 5_000_000})
        assert result.passed is True
        assert "Low float" in result.reason or "within limit" in result.reason

    def test_high_float_fails(self):
        pillar = FloatPillar({"max_shares": 20_000_000})
        result = pillar.evaluate("TEST", {"float_shares": 50_000_000})
        assert result.passed is False
        assert "exceeds" in result.reason

    def test_missing_float_fails(self):
        pillar = FloatPillar({"max_shares": 20_000_000})
        result = pillar.evaluate("TEST", {"float_shares": None})
        assert result.passed is False
        assert "unavailable" in result.reason

    def test_at_boundary_passes(self):
        pillar = FloatPillar({"max_shares": 20_000_000})
        result = pillar.evaluate("TEST", {"float_shares": 20_000_000})
        assert result.passed is True


class TestMomentumPillar:
    """Tests for MomentumPillar (early-session velocity)."""

    def test_strong_momentum_passes(self):
        pillar = MomentumPillar({
            "min_pct_move": 10.0,
            "min_early_session_rvol": 5.0,
        })
        result = pillar.evaluate("TEST", {
            "price": 11.0,
            "prev_close": 10.0,  # +10%
            "intraday_volume": 5_000_000,
            "avg_volume": 100_000,  # RVol = 50x (normalized)
            "timestamp": datetime.now(timezone.utc),
        })
        assert result.passed is True

    def test_low_pct_move_fails(self):
        pillar = MomentumPillar({
            "min_pct_move": 10.0,
            "min_early_session_rvol": 5.0,
        })
        result = pillar.evaluate("TEST", {
            "price": 10.50,
            "prev_close": 10.0,  # +5%
            "intraday_volume": 10_000_000,
            "avg_volume": 1_000_000,
            "timestamp": datetime.now(timezone.utc),
        })
        assert result.passed is False
        assert "below threshold" in result.reason

    def test_missing_price_fails(self):
        pillar = MomentumPillar({"min_pct_move": 10.0})
        result = pillar.evaluate("TEST", {"prev_close": 10.0})
        assert result.passed is False
        assert "unavailable" in result.reason
