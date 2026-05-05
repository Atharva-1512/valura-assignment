from pydantic import BaseModel
from typing import Dict, List, Optional, Any


class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    portfolio: Optional[List[Dict[str, Any]]] = None


class SafetyResult(BaseModel):
    safe: bool
    category: Optional[str] = None
    message: Optional[str] = None


class ClassifierResult(BaseModel):
    intent: str
    entities: Dict[str, Any]
    agent: str
    safety: str


class AgentResponse(BaseModel):
    agent: str
    intent: str
    message: str
    data: Optional[Dict[str, Any]] = None


class PortfolioHealthData(BaseModel):
    concentration_risk: Dict[str, Any]
    performance: Dict[str, Any]
    benchmark_comparison: Dict[str, Any]
    observations: List[str]
    disclaimer: str


class PortfolioHolding(BaseModel):
    symbol: str
    shares: float
    price: Optional[float] = None


class PortfolioAnalysis(BaseModel):
    holdings: List[PortfolioHolding]
    total_value: float
    analysis: PortfolioHealthData