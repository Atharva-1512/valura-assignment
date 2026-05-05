import logging
from typing import Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for fetching market data."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.mock_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 300.0,
            "TSLA": 200.0,
            "AMZN": 3000.0,
        }

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        if self.use_mock:
            return self.mock_prices.get(symbol.upper(), 100.0)  # Default mock price

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None