from abc import ABC, abstractmethod
from typing import Any, Optional
from src.models import ClassifierResult


class BaseAgent(ABC):
    """Base class for all agents."""

    @abstractmethod
    def execute(self, classifier_result: ClassifierResult, portfolio: Optional[list] = None) -> dict:
        """Execute agent logic and return result."""
        pass