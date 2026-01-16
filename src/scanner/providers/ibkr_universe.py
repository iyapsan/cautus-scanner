"""
IBKR Universe Provider using reqScannerSubscription.

Provides dynamic ticker discovery via IBKR's market scanner API.
This is a v1.1 feature that replaces CSV-based universe for production.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IBKRUniverseProvider:
    """
    Dynamic universe discovery via IBKR's market scanner.
    
    Uses reqScannerSubscription to find candidates matching:
    - Price range filter (pre-screen)
    - Volume filter (pre-screen)
    - Exchange filter (US equities only)
    
    Returns streaming symbols that pass broker-side filters.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4002,
        client_id: int = 2,
        market_data_type: int = 3,
        # Scanner pre-filters
        price_min: float = 2.0,
        price_max: float = 20.0,
        volume_min: int = 500_000,
        percent_change_min: float = 5.0,
        max_results: int = 50,
    ) -> None:
        """
        Initialize IBKR universe scanner.

        Args:
            host: TWS/Gateway host
            port: TWS/Gateway port
            client_id: Unique client ID (different from market data provider)
            market_data_type: 1=live, 3=delayed
            price_min: Minimum price filter
            price_max: Maximum price filter
            volume_min: Minimum volume filter
            percent_change_min: Minimum % gain filter
            max_results: Maximum results to return
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.market_data_type = market_data_type
        self.price_min = price_min
        self.price_max = price_max
        self.volume_min = volume_min
        self.percent_change_min = percent_change_min
        self.max_results = max_results
        
        self._ib: Any = None
        self._connected = False
        self._universe: list[str] = []
        self._subscription: Any = None
        
        logger.info(
            f"IBKRUniverseProvider initialized "
            f"(price=${price_min}-${price_max}, vol>{volume_min:,}, gain>{percent_change_min}%)"
        )

    def _ensure_connected(self) -> None:
        """Ensure connection to IBKR."""
        if self._connected and self._ib and self._ib.isConnected():
            return

        try:
            from ib_async import IB

            self._ib = IB()
            self._ib.connect(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=15,
            )
            self._connected = True
            
            # Set market data type
            self._ib.reqMarketDataType(self.market_data_type)
            
            logger.info(f"IBKRUniverseProvider connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"IBKR connection failed: {e}") from e

    def _create_scanner_subscription(self) -> Any:
        """Create scanner subscription with filters."""
        from ib_async import ScannerSubscription

        # Top % Gainers with filters
        sub = ScannerSubscription(
            instrument="STK",
            locationCode="STK.US.MAJOR",
            scanCode="TOP_PERC_GAIN",
        )
        
        # Set filter criteria
        sub.abovePrice = self.price_min
        sub.belowPrice = self.price_max
        sub.aboveVolume = self.volume_min
        sub.numberOfRows = self.max_results
        
        return sub

    def get_universe(self) -> list[str]:
        """
        Get list of symbols from IBKR scanner.
        
        Returns:
            List of symbols matching scanner criteria
        """
        self._ensure_connected()
        
        try:
            subscription = self._create_scanner_subscription()
            
            # Request scanner data
            results = self._ib.reqScannerData(subscription)
            
            # Extract symbols
            symbols = []
            for item in results:
                if hasattr(item, 'contractDetails') and item.contractDetails:
                    contract = item.contractDetails.contract
                    symbols.append(contract.symbol)
            
            self._universe = symbols
            logger.info(f"Scanner returned {len(symbols)} symbols")
            
            return symbols
            
        except Exception as e:
            logger.error(f"Scanner request failed: {e}")
            return self._universe  # Return cached universe on error

    def subscribe(self, callback: callable) -> None:
        """
        Subscribe to streaming scanner updates.
        
        Args:
            callback: Function called with updated symbol list
        """
        self._ensure_connected()
        
        subscription = self._create_scanner_subscription()
        
        def on_scan_data(data):
            symbols = [
                item.contractDetails.contract.symbol
                for item in data
                if item.contractDetails
            ]
            self._universe = symbols
            callback(symbols)
        
        # Subscribe to scanner
        self._ib.reqScannerSubscription(subscription)
        self._ib.scannerDataEvent += on_scan_data
        
        logger.info("Subscribed to scanner updates")

    def refresh(self) -> None:
        """Refresh universe by re-querying scanner."""
        self.get_universe()

    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self._ib and self._connected:
            self._ib.disconnect()
            self._connected = False
            logger.info("IBKRUniverseProvider disconnected")

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.disconnect()
