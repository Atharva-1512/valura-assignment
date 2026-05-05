import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from src.models import ClassifierResult


class IntentClassifier:
    """LLM-based intent classifier."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", "mock-key"))
        self.model = "gpt-4o-mini"
        
        self.system_prompt = (
            "You are an intent classification agent for a wealth management platform. "
            "Given a user query and optional conversation history, classify the user's intent. "
            "You must extract relevant entities (like tickers, amounts, etc.). "
            "You must also determine which agent should handle this request. "
            "Valid agents include: 'portfolio_health', 'market_news', 'trading_advisor', "
            "'market_research', 'investment_strategy', 'financial_calculator', 'general'. "
            "Finally, provide an informational safety verdict ('safe', 'warning', 'unsafe'). "
            "If the user asks 'how is my portfolio doing?' or similar, the agent is 'portfolio_health'. "
            "Ensure you always output valid JSON adhering to the provided schema."
        )

    def classify(self, query: str, conversation_memory: Optional[Dict[str, Any]] = None) -> ClassifierResult:
        """Classify intent with a single LLM call."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_memory and "history" in conversation_memory:
                for msg in conversation_memory["history"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                    
            messages.append({"role": "user", "content": query})

            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=ClassifierResult,
            )
            
            parsed_result = response.choices[0].message.parsed
            
            # Fallback if parsing didn't throw but returned None
            if not parsed_result:
                raise ValueError("Parsed result is None")
                
            return parsed_result

        except Exception as e:
            # Fallback behavior
            return ClassifierResult(
                intent="unknown",
                entities={},
                agent="general",
                safety="safe"
            )