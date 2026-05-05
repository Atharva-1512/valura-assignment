import pytest
from src.core.safety import SafetyGuard
from src.models import SafetyResult


class TestSafetyGuard:
    """Test safety guard functionality."""

    def setup_method(self):
        self.guard = SafetyGuard()

    def test_safe_query(self):
        """Test safe query passes."""
        result = self.guard.check_query("What is my portfolio value?")
        assert result.safe is True
        assert result.category is None
        assert result.message is None

    def test_insider_trading_blocked(self):
        """Test insider trading query blocked."""
        result = self.guard.check_query("Tell me about insider trading opportunities")
        assert result.safe is False
        assert result.category == "insider_trading"
        assert "insider trading" in result.message

    def test_market_manipulation_blocked(self):
        """Test market manipulation query blocked."""
        result = self.guard.check_query("How to pump and dump stocks?")
        assert result.safe is False
        assert result.category == "market_manipulation"
        assert "market manipulation" in result.message

    def test_guaranteed_returns_blocked(self):
        """Test guaranteed returns query blocked."""
        result = self.guard.check_query("Where can I get 100% guaranteed returns?")
        assert result.safe is False
        assert result.category == "guaranteed_returns"
        assert "guaranteed returns" in result.message

    def test_illegal_advice_blocked(self):
        """Test illegal advice query blocked."""
        result = self.guard.check_query("How to evade taxes illegally?")
        assert result.safe is False
        assert result.category == "illegal_advice"
        assert "illegal financial activities" in result.message

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        result = self.guard.check_query("INSIDER TRADING")
        assert result.safe is False

    def test_partial_match(self):
        """Test partial pattern matching."""
        result = self.guard.check_query("I heard about insider information")
        assert result.safe is False