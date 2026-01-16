"""
IBKR Market Data Provider - Production implementation.

Uses ib_async (actively maintained fork of ib_insync) to connect to IBKR TWS/Gateway.

Requirements:
- TWS or IB Gateway running locally
- API connections enabled in TWS/Gateway settings
- Market data subscriptions for target symbols
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import backoff

logger = logging.getLogger(__name__)


class IBKRMarketDataProvider:
    """
    IBKR TWS/Gateway market data adapter.
    
    Powers Price, Momentum, Volume pillars with real-time data.
    
    Connection:
    - TWS: port 7497 (paper) / 7496 (live)
    - IB Gateway: port 4002 (paper) / 4001 (live)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        timeout: int = 10,
        market_data_type: int = 1,
    ) -> None:
        """
        Initialize IBKR connection parameters.

        Args:
            host: TWS/Gateway host (default: localhost)
            port: TWS/Gateway port (7497=TWS paper, 4002=Gateway paper)
            client_id: Unique client ID for this connection
            timeout: Connection timeout in seconds
            market_data_type: 1=Live (default), 2=Frozen, 3=Delayed, 4=Delayed-Frozen
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self.market_data_type = market_data_type
        self._ib: Any = None  # IB instance
        self._connected = False
        self._contract_cache: dict[str, Any] = {}
        
        data_type_names = {1: "live", 2: "frozen", 3: "delayed", 4: "delayed-frozen"}
        logger.info(f"IBKRMarketDataProvider initialized (host={host}, port={port}, data_type={data_type_names.get(market_data_type, 'unknown')})")

    def _ensure_connected(self) -> None:
        """Ensure connection to IBKR is active."""
        if self._connected and self._ib and self._ib.isConnected():
            return

        try:
            from ib_async import IB

            self._ib = IB()
            self._ib.connect(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=self.timeout,
            )
            self._connected = True
            
            # Set market data type (1=Live, 2=Frozen, 3=Delayed, 4=Delayed-Frozen)
            self._ib.reqMarketDataType(self.market_data_type)
            
            data_type_names = {1: "live", 2: "frozen", 3: "delayed", 4: "delayed-frozen"}
            logger.info(f"Connected to IBKR at {self.host}:{self.port} (data_type={data_type_names.get(self.market_data_type, 'unknown')})")
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise ConnectionError(f"IBKR connection failed: {e}") from e

    def _get_contract(self, symbol: str) -> Any:
        """Get or create a stock contract for symbol."""
        if symbol in self._contract_cache:
            return self._contract_cache[symbol]

        from ib_async import Stock

        # US stock on SMART routing
        contract = Stock(symbol, "SMART", "USD")
        
        # Qualify the contract to get full details
        self._ensure_connected()
        qualified = self._ib.qualifyContracts(contract)
        
        if not qualified:
            raise ValueError(f"Could not qualify contract for {symbol}")

        self._contract_cache[symbol] = qualified[0]
        return qualified[0]

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_last_price(self, symbol: str) -> float:
        """
        Get current market price for symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Current price as float
        """
        self._ensure_connected()
        contract = self._get_contract(symbol)

        # Request market data snapshot
        ticker = self._ib.reqMktData(contract, "", snapshot=True)
        self._ib.sleep(1)  # Wait for data
        
        # Get last price (prefer last, fallback to close)
        price = ticker.last
        if price is None or price <= 0:
            price = ticker.close
        if price is None or price <= 0:
            price = ticker.marketPrice()

        # Cancel market data subscription
        self._ib.cancelMktData(contract)

        if price is None or price <= 0:
            raise ValueError(f"Could not get price for {symbol}")

        return float(price)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_prev_close(self, symbol: str) -> float:
        """
        Get previous day's closing price.

        Args:
            symbol: Stock symbol

        Returns:
            Previous close price
        """
        self._ensure_connected()
        contract = self._get_contract(symbol)

        # Request market data snapshot
        ticker = self._ib.reqMktData(contract, "", snapshot=True)
        self._ib.sleep(1)

        close = ticker.close
        
        self._ib.cancelMktData(contract)

        if close is None or close <= 0:
            raise ValueError(f"Could not get previous close for {symbol}")

        return float(close)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_intraday_volume(self, symbol: str) -> int:
        """
        Get today's trading volume so far.

        Args:
            symbol: Stock symbol

        Returns:
            Intraday volume as integer
        """
        self._ensure_connected()
        contract = self._get_contract(symbol)

        # Request market data snapshot
        ticker = self._ib.reqMktData(contract, "", snapshot=True)
        self._ib.sleep(1)

        volume = ticker.volume
        
        self._ib.cancelMktData(contract)

        if volume is None or volume < 0:
            return 0

        return int(volume)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_historical_daily_volume(self, symbol: str, lookback_days: int = 30) -> list[int]:
        """
        Get daily volume for past N trading days.

        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back

        Returns:
            List of daily volumes (oldest to newest)
        """
        self._ensure_connected()
        contract = self._get_contract(symbol)

        # Calculate duration string (e.g., "30 D" for 30 days)
        duration = f"{lookback_days} D"

        # Request historical bars
        bars = self._ib.reqHistoricalData(
            contract,
            endDateTime="",  # Now
            durationStr=duration,
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,  # Regular trading hours only
            formatDate=1,
        )

        if not bars:
            logger.warning(f"No historical data for {symbol}")
            return []

        # Extract volumes
        volumes = [int(bar.volume) for bar in bars]
        
        return volumes

    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self._ib and self._connected:
            self._ib.disconnect()
            self._connected = False
            self._contract_cache.clear()
            logger.info("Disconnected from IBKR")

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.disconnect()
