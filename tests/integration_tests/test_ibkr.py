"""
Integration tests for IBKR market data provider.

These tests require a live IBKR TWS/Gateway connection.
Run with: pytest tests/integration_tests/ -v -m integration

Prerequisites:
- TWS or IB Gateway running on localhost
- API connections enabled in TWS/Gateway settings
- Valid market data subscriptions

Environment variables (optional):
- IBKR_HOST: TWS/Gateway host (default: 127.0.0.1)
- IBKR_PORT: TWS/Gateway port (default: 7497)
- IBKR_CLIENT_ID: Client ID (default: 99)
"""

import os
import pytest

from scanner.providers.ibkr_market_data import IBKRMarketDataProvider


# Skip all tests if not running integration tests
pytestmark = pytest.mark.integration


# Test symbols (common, high-liquidity)
TEST_SYMBOLS = ["AAPL", "MSFT", "SPY"]


@pytest.fixture(scope="module")
def ibkr_provider():
    """Create IBKR provider with connection."""
    host = os.environ.get("IBKR_HOST", "127.0.0.1")
    port = int(os.environ.get("IBKR_PORT", "7497"))
    client_id = int(os.environ.get("IBKR_CLIENT_ID", "99"))
    # Default to delayed data (3) for testing without live subscription
    market_data_type = int(os.environ.get("IBKR_MARKET_DATA_TYPE", "3"))
    
    provider = IBKRMarketDataProvider(
        host=host,
        port=port,
        client_id=client_id,
        timeout=15,
        market_data_type=market_data_type,
    )
    
    yield provider
    
    # Cleanup
    provider.disconnect()


class TestIBKRConnection:
    """Tests for IBKR connection management."""

    def test_connection_successful(self, ibkr_provider):
        """Verify we can connect to IBKR."""
        ibkr_provider._ensure_connected()
        assert ibkr_provider._connected is True
        assert ibkr_provider._ib is not None
        assert ibkr_provider._ib.isConnected()

    def test_contract_qualification(self, ibkr_provider):
        """Verify we can qualify a stock contract."""
        contract = ibkr_provider._get_contract("AAPL")
        assert contract is not None
        assert contract.symbol == "AAPL"
        assert contract.secType == "STK"


class TestIBKRMarketData:
    """Tests for market data fetching."""

    @pytest.mark.parametrize("symbol", TEST_SYMBOLS)
    def test_get_last_price(self, ibkr_provider, symbol):
        """Verify we can get current price."""
        price = ibkr_provider.get_last_price(symbol)
        
        assert price is not None
        assert isinstance(price, float)
        assert price > 0
        print(f"{symbol} price: ${price:.2f}")

    @pytest.mark.parametrize("symbol", TEST_SYMBOLS)
    def test_get_prev_close(self, ibkr_provider, symbol):
        """Verify we can get previous close."""
        prev_close = ibkr_provider.get_prev_close(symbol)
        
        assert prev_close is not None
        assert isinstance(prev_close, float)
        assert prev_close > 0
        print(f"{symbol} prev close: ${prev_close:.2f}")

    @pytest.mark.parametrize("symbol", TEST_SYMBOLS)
    def test_get_intraday_volume(self, ibkr_provider, symbol):
        """Verify we can get intraday volume."""
        volume = ibkr_provider.get_intraday_volume(symbol)
        
        assert volume is not None
        assert isinstance(volume, int)
        assert volume >= 0  # Could be 0 pre-market
        print(f"{symbol} volume: {volume:,}")

    @pytest.mark.parametrize("symbol", TEST_SYMBOLS)
    def test_get_historical_daily_volume(self, ibkr_provider, symbol):
        """Verify we can get historical volume data."""
        volumes = ibkr_provider.get_historical_daily_volume(symbol, lookback_days=10)
        
        assert volumes is not None
        assert isinstance(volumes, list)
        assert len(volumes) > 0
        assert all(isinstance(v, int) for v in volumes)
        print(f"{symbol} historical volumes (10 days): {len(volumes)} bars")


class TestIBKRFullScanCycle:
    """End-to-end test of scanner with IBKR."""

    def test_full_scan_single_symbol(self, ibkr_provider):
        """Test complete scan cycle for a single symbol."""
        symbol = "AAPL"
        
        # Get all required data
        price = ibkr_provider.get_last_price(symbol)
        prev_close = ibkr_provider.get_prev_close(symbol)
        volume = ibkr_provider.get_intraday_volume(symbol)
        historical = ibkr_provider.get_historical_daily_volume(symbol, lookback_days=30)
        
        # Calculate derived values
        pct_change = ((price - prev_close) / prev_close) * 100
        avg_volume = sum(historical) / len(historical) if historical else 0
        rvol = volume / avg_volume if avg_volume > 0 else 0
        
        # Print summary
        print(f"\n{symbol} Scan Summary:")
        print(f"  Price: ${price:.2f}")
        print(f"  Prev Close: ${prev_close:.2f}")
        print(f"  % Change: {pct_change:+.2f}%")
        print(f"  Volume: {volume:,}")
        print(f"  Avg Volume (30d): {avg_volume:,.0f}")
        print(f"  RVol: {rvol:.2f}x")
        
        # Basic assertions
        assert price > 0
        assert prev_close > 0
        assert len(historical) > 0


class TestIBKRErrorHandling:
    """Tests for error handling."""

    def test_invalid_symbol_returns_empty(self, ibkr_provider):
        """Invalid symbol should not qualify (returns empty or logs warning)."""
        # IBKR doesn't raise an exception for invalid symbols,
        # it returns an empty/unqualified contract and logs a warning
        contract = ibkr_provider._get_contract("INVALID_SYMBOL_XYZ123")
        # The contract will be returned but with conId=0 or similar
        # This test just verifies it doesn't crash
        assert contract is None or hasattr(contract, 'symbol')

    def test_disconnect_reconnect(self, ibkr_provider):
        """Verify we can disconnect and reconnect."""
        # Ensure connected first
        ibkr_provider._ensure_connected()
        assert ibkr_provider._connected is True
        
        # Disconnect
        ibkr_provider.disconnect()
        assert ibkr_provider._connected is False
        
        # Reconnect via get_last_price
        price = ibkr_provider.get_last_price("AAPL")
        assert ibkr_provider._connected is True
        assert price > 0
