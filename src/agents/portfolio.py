import logging
from typing import Dict, Any, Optional, List
from src.models import ClassifierResult, PortfolioHealthData, PortfolioHolding
from src.agents.base import BaseAgent
from src.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class PortfolioHealthAgent(BaseAgent):
    """Portfolio health analysis agent."""

    def __init__(self, market_service: Optional[MarketDataService] = None):
        self.market_service = market_service or MarketDataService()

    def execute(self, classifier_result: ClassifierResult, portfolio: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Execute portfolio health analysis."""
        if not portfolio:
            return self._empty_portfolio_response()

        try:
            holdings = self._parse_portfolio(portfolio)
            analysis = self._analyze_portfolio(holdings)

            return {
                "holdings": [h.model_dump() for h in holdings],
                "total_value": sum(h.shares * (h.price or 0) for h in holdings),
                "analysis": analysis.model_dump()
            }

        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            return self._error_response(str(e))

    def _parse_portfolio(self, portfolio: List[Dict[str, Any]]) -> List[PortfolioHolding]:
        """Parse portfolio data into holdings."""
        holdings = []
        for item in portfolio:
            try:
                holding = PortfolioHolding(
                    symbol=item["symbol"],
                    shares=float(item["shares"]),
                    price=item.get("price")
                )
                holdings.append(holding)
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid portfolio item: {item}, error: {e}")
                continue
        return holdings

    def _analyze_portfolio(self, holdings: List[PortfolioHolding]) -> PortfolioHealthData:
        """Analyze portfolio health."""
        if not holdings:
            return PortfolioHealthData(
                concentration_risk={"level": "none", "details": "No holdings"},
                performance={"status": "unknown"},
                benchmark_comparison={"vs_sp500": "N/A"},
                observations=["No portfolio data available"],
                disclaimer="Analysis based on provided data"
            )

        # Get current prices if not provided
        for holding in holdings:
            if holding.price is None:
                holding.price = self.market_service.get_current_price(holding.symbol)

        total_value = sum(h.shares * h.price for h in holdings if h.price)

        # Concentration risk
        concentration = self._calculate_concentration(holdings, total_value)

        # Performance (simplified)
        performance = self._assess_performance(holdings)

        # Benchmark comparison (mock)
        benchmark = self._compare_to_benchmark(holdings)

        # Observations
        observations = self._generate_observations(holdings, concentration)

        return PortfolioHealthData(
            concentration_risk=concentration,
            performance=performance,
            benchmark_comparison=benchmark,
            observations=observations,
            disclaimer="This is not financial advice. Past performance does not guarantee future results."
        )

    def _calculate_concentration(self, holdings: List[PortfolioHolding], total_value: float) -> Dict[str, Any]:
        """Calculate concentration risk."""
        if total_value == 0:
            return {"level": "unknown", "details": "No value"}

        # Sort by value
        holding_values = [(h.symbol, h.shares * h.price) for h in holdings if h.price]
        holding_values.sort(key=lambda x: x[1], reverse=True)

        if not holding_values:
            return {"level": "unknown", "details": "No priced holdings"}

        top_holding_pct = (holding_values[0][1] / total_value) * 100

        if top_holding_pct > 50:
            level = "high"
        elif top_holding_pct > 20:
            level = "moderate"
        else:
            level = "low"

        return {
            "level": level,
            "top_holding": f"{holding_values[0][0]} ({top_holding_pct:.1f}%)",
            "details": f"Top holding represents {top_holding_pct:.1f}% of portfolio"
        }

    def _assess_performance(self, holdings: List[PortfolioHolding]) -> Dict[str, Any]:
        """Assess portfolio performance (simplified)."""
        # Mock performance assessment
        return {
            "status": "stable",
            "details": "Portfolio appears stable based on current holdings"
        }

    def _compare_to_benchmark(self, holdings: List[PortfolioHolding]) -> Dict[str, Any]:
        """Compare to benchmark (mock)."""
        return {
            "vs_sp500": "Underperforming by 2.3%",
            "details": "Based on simplified comparison"
        }

    def _generate_observations(self, holdings: List[PortfolioHolding], concentration: Dict[str, Any]) -> List[str]:
        """Generate key observations."""
        observations = []

        if concentration["level"] == "high":
            observations.append("High concentration risk detected. Consider diversification.")

        if len(holdings) < 5:
            observations.append("Limited diversification. Consider adding more assets.")

        observations.append("Regular portfolio review recommended.")

        return observations[:3]  # Max 3 observations

    def _empty_portfolio_response(self) -> Dict[str, Any]:
        """Response for empty portfolio oriented toward BUILD."""
        return {
            "holdings": [],
            "total_value": 0,
            "analysis": PortfolioHealthData(
                concentration_risk={"level": "none", "details": "No investments yet. This is a clean slate to build a diversified portfolio."},
                performance={"status": "N/A", "details": "No historical performance yet."},
                benchmark_comparison={"vs_sp500": "N/A"},
                observations=[
                    "Your portfolio is currently empty. Let's start building your wealth.",
                    "Consider defining your financial goals and risk tolerance first.",
                    "A good starting point is a diversified index fund or ETF."
                ],
                disclaimer="This is not financial advice. Investing involves risk."
            ).model_dump()
        }

    def _error_response(self, error: str) -> Dict[str, Any]:
        """Error response."""
        return {
            "error": error,
            "analysis": PortfolioHealthData(
                concentration_risk={"level": "error"},
                performance={"status": "error"},
                benchmark_comparison={"vs_sp500": "N/A"},
                observations=["Analysis failed due to error"],
                disclaimer="This is not financial advice."
            ).model_dump()
        }