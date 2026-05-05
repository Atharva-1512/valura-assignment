import pytest
from unittest.mock import patch, MagicMock
from src.core.classifier import IntentClassifier
from src.models import ClassifierResult


class TestIntentClassifier:
    """Test intent classifier functionality."""

    def setup_method(self, method=None):
        # We don't actually need to mock in setup if we patch in each test,
        # but since we initialized IntentClassifier, we can let it use the fake key.
        with patch("src.core.classifier.OpenAI"):
            self.classifier = IntentClassifier(api_key="fake-key")

    @patch("src.core.classifier.OpenAI")
    def test_portfolio_query_classification(self, mock_openai):
        """Test portfolio query classification."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Setup mock response
        mock_response = MagicMock()
        mock_parsed = ClassifierResult(
            intent="analyze_portfolio",
            entities={},
            agent="portfolio_health",
            safety="safe"
        )
        mock_response.choices[0].message.parsed = mock_parsed
        mock_client.beta.chat.completions.parse.return_value = mock_response

        # Re-initialize with mocked client
        classifier = IntentClassifier(api_key="fake-key")
        classifier.client = mock_client

        result = classifier.classify("Analyze my portfolio health")
        assert result.intent == "analyze_portfolio"
        assert result.agent == "portfolio_health"
        assert result.safety == "safe"

    @patch("src.core.classifier.OpenAI")
    def test_fallback_on_error(self, mock_openai):
        """Test fallback behavior."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")

        classifier = IntentClassifier(api_key="fake-key")
        classifier.client = mock_client

        result = classifier.classify("Any query")
        assert result.intent == "unknown"
        assert result.agent == "general"
        assert result.safety == "safe"