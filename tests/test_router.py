import pytest
from src.core.router import Router
from src.models import ClassifierResult, AgentResponse


class TestRouter:
    """Test router functionality."""

    def setup_method(self):
        self.router = Router()

    def test_portfolio_health_routing(self):
        """Test routing to portfolio health agent."""
        classifier_result = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        response = self.router.route(classifier_result, [])
        assert response.agent == "portfolio_health"
        assert response.intent == "analyze_portfolio"
        assert "data" in response.model_dump()

    def test_stub_agent_routing(self):
        """Test routing to stub agent."""
        classifier_result = ClassifierResult(
            intent="get_news",
            entities={"topic": "market"},
            agent="market_news",
            safety="safe"
        )
        response = self.router.route(classifier_result)
        assert response.agent == "market_news"
        assert response.intent == "get_news"
        assert response.message == "Not implemented in this build"
        assert response.data is not None
        assert "entities" in response.data
        assert response.data["entities"] == {"topic": "market"}

    def test_unknown_agent_routing(self):
        """Test routing to unknown agent."""
        classifier_result = ClassifierResult(
            intent="unknown",
            entities={},
            agent="unknown_agent",
            safety="safe"
        )
        response = self.router.route(classifier_result)
        assert response.agent == "unknown_agent"
        assert response.message == "Not implemented in this build"