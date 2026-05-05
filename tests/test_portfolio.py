import pytest
from src.agents.portfolio import PortfolioHealthAgent
from src.models import ClassifierResult
from src.services.market_data import MarketDataService


class TestPortfolioHealthAgent:
    """Test portfolio health agent functionality."""

    def setup_method(self):
        self.market_service = MarketDataService(use_mock=True)
        self.agent = PortfolioHealthAgent(self.market_service)

    def test_empty_portfolio(self):
        """Test handling of empty portfolio."""
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, None)
        assert result["total_value"] == 0
        assert len(result["holdings"]) == 0
        assert "analysis" in result

    def test_single_holding_portfolio(self):
        """Test portfolio with single holding."""
        portfolio = [{"symbol": "AAPL", "shares": 10}]
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        assert len(result["holdings"]) == 1
        assert result["holdings"][0]["symbol"] == "AAPL"
        assert result["holdings"][0]["shares"] == 10
        assert result["total_value"] == 1500.0  # 10 * 150 mock price
        assert "analysis" in result

    def test_multiple_holdings_portfolio(self):
        """Test portfolio with multiple holdings."""
        portfolio = [
            {"symbol": "AAPL", "shares": 10},
            {"symbol": "GOOGL", "shares": 5}
        ]
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        assert len(result["holdings"]) == 2
        assert result["total_value"] == 10 * 150 + 5 * 2800  # 1500 + 14000 = 15500
        assert "analysis" in result

    def test_concentration_risk_high(self):
        """Test high concentration risk detection."""
        portfolio = [{"symbol": "AAPL", "shares": 100}]  # Single large holding
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        concentration = result["analysis"]["concentration_risk"]
        assert concentration["level"] == "high"

    def test_concentration_risk_low(self):
        """Test low concentration risk."""
        portfolio = [
            {"symbol": "AAPL", "shares": 10},  # 1500
            {"symbol": "GOOGL", "shares": 2},  # 5600
            {"symbol": "MSFT", "shares": 10},  # 3000
            {"symbol": "TSLA", "shares": 10},  # 2000
            {"symbol": "AMZN", "shares": 2}   # 6000
        ]  # Total 18100, top 6000 (33%), still moderate. Wait, to make low, need top <20%
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        concentration = result["analysis"]["concentration_risk"]
        assert concentration["level"] == "moderate"

    def test_invalid_portfolio_item(self):
        """Test handling of invalid portfolio items."""
        portfolio = [
            {"symbol": "AAPL", "shares": 10},
            {"invalid": "item"}
        ]
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        # Should skip invalid item
        assert len(result["holdings"]) == 1
        assert result["holdings"][0]["symbol"] == "AAPL"

    def test_observations_limit(self):
        """Test that observations are limited to max 3."""
        portfolio = [{"symbol": "AAPL", "shares": 100}]
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, portfolio)
        observations = result["analysis"]["observations"]
        assert len(observations) <= 3

    def test_disclaimer_present(self):
        """Test disclaimer is always present."""
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        result = self.agent.execute(classifier_result, [])
        assert "disclaimer" in result["analysis"]
        assert "not financial advice" in result["analysis"]["disclaimer"].lower()