import re
from typing import Optional
from src.models import SafetyResult


class SafetyGuard:
    """Pure Python safety guard for fintech queries."""

    # Patterns for blocked content
    INSIDER_TRADING_PATTERNS = [
        r"insider.*trading",
        r"non.public.*information",
        r"material.*non.public",
        r"confidential.*trading",
        r"insider.*information",
    ]

    MARKET_MANIPULATION_PATTERNS = [
        r"pump.*dump",
        r"manipulate.*market",
        r"artificial.*price",
        r"corner.*market",
        r"wash.*trading",
    ]

    GUARANTEED_RETURNS_PATTERNS = [
        r"guaranteed.*return",
        r"risk.free.*investment",
        r"100%.*return",
        r"no.*risk.*investment",
    ]

    ILLEGAL_ADVICE_PATTERNS = [
        r"tax.*evasion",
        r"money.*laundering",
        r"fraudulent.*scheme",
        r"illegal.*investment",
        r"evade.*tax",
        r"illegal.*advice",
    ]

    def __init__(self):
        self.patterns = {
            "insider_trading": self.INSIDER_TRADING_PATTERNS,
            "market_manipulation": self.MARKET_MANIPULATION_PATTERNS,
            "guaranteed_returns": self.GUARANTEED_RETURNS_PATTERNS,
            "illegal_advice": self.ILLEGAL_ADVICE_PATTERNS,
        }

    def check_query(self, query: str) -> SafetyResult:
        """Check if query is safe. Returns SafetyResult."""
        query_lower = query.lower()

        # Allow educational queries
        educational_patterns = [
            r"what is", r"explain", r"define", r"meaning of", r"how does.*work", r"tell me about the concept"
        ]
        is_educational = any(re.search(pat, query_lower) for pat in educational_patterns)

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    if is_educational:
                        # Tradeoff: Let it pass if it's explicitly educational
                        continue
                    return SafetyResult(
                        safe=False,
                        category=category,
                        message=self._get_rejection_message(category)
                    )

        return SafetyResult(safe=True)

    def _get_rejection_message(self, category: str) -> str:
        """Get category-specific rejection message."""
        messages = {
            "insider_trading": "I cannot assist with queries involving insider trading or non-public information.",
            "market_manipulation": "I cannot assist with queries involving market manipulation or artificial price movements.",
            "guaranteed_returns": "I cannot provide advice on guaranteed returns or risk-free investments.",
            "illegal_advice": "I cannot assist with queries involving illegal financial activities.",
        }
        return messages.get(category, "This query violates our safety guidelines.")