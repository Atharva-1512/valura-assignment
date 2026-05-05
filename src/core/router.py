from typing import Dict, Any, Optional
from src.models import ClassifierResult, AgentResponse
from src.agents.base import BaseAgent
from src.agents.portfolio import PortfolioHealthAgent


class Router:
    """Routes queries to appropriate agents."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "portfolio_health": PortfolioHealthAgent(),
        }

    def route(self, classifier_result: ClassifierResult, portfolio: Optional[list] = None) -> AgentResponse:
        """Route to agent based on classifier result."""
        agent_name = classifier_result.agent

        if agent_name in self.agents:
            # Call real agent
            agent = self.agents[agent_name]
            result = agent.execute(classifier_result, portfolio)
            return AgentResponse(
                agent=agent_name,
                intent=classifier_result.intent,
                message="Agent executed successfully",
                data=result
            )
        else:
            # Return stub for unimplemented agents
            return AgentResponse(
                agent=agent_name,
                intent=classifier_result.intent,
                message="Not implemented in this build",
                data={
                    "entities": classifier_result.entities
                }
            )