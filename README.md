# Fintech AI Router

A production-grade AI agent routing system for fintech platforms, built with FastAPI and Python 3.11+.

## Overview

This system processes user queries through a multi-stage pipeline:

1. **Safety Guard** - Local rule-based filtering (<10ms)
2. **Intent Classifier** - Single LLM call for structured classification
3. **Router** - Routes to appropriate agent
4. **Agent Execution** - Executes portfolio health analysis
5. **Streaming Response** - Server-Sent Events (SSE) for real-time updates

## Architecture

### Clean Architecture

```
src/
├── main.py              # FastAPI application entry point
├── api/
│   └── routes.py        # API endpoints with SSE streaming
├── core/
│   ├── safety.py        # Pure Python safety guard
│   ├── classifier.py    # Mock LLM intent classifier
│   └── router.py        # Agent routing logic
├── agents/
│   ├── base.py          # Abstract agent base class
│   └── portfolio.py     # Portfolio health analysis agent
├── models/
│   └── __init__.py      # Pydantic data models
├── services/
│   └── market_data.py   # Market data service (mock/yfinance)
└── utils/
    └── __init__.py      # Utility functions
```

### Design Decisions

#### Safety Guard
- **Pure Python implementation** - No external dependencies for speed
- **Deterministic rules** - Consistent blocking behavior
- **Category-specific messages** - Clear rejection reasons
- **Fast execution** - <10ms latency

#### Intent Classifier
- **Single LLM call** - Minimizes API usage and latency
- **Structured output** - JSON format for reliable parsing
- **Fallback handling** - Graceful degradation on failures
- **Mock implementation** - No API keys required for testing

#### Router
- **Agent registry** - Easy to add new agents
- **Stub responses** - Consistent format for unimplemented agents
- **Dependency injection** - Testable and modular

#### Portfolio Health Agent
- **Comprehensive analysis** - Concentration risk, performance, benchmarks
- **Graceful empty handling** - Works with missing portfolio data
- **Simple language** - Beginner-friendly explanations
- **Mock market data** - No real API dependencies

#### Streaming
- **Server-Sent Events** - Real-time partial responses
- **Event types** - Structured event categorization
- **Error handling** - SSE error events
- **Timeout management** - Prevents hanging connections

## Performance Constraints

- **First token**: <2 seconds
- **Total response**: <6 seconds
- **LLM calls**: 1 per query (classifier only)
- **Safety check**: <10ms

## Setup

### Prerequisites

- Python 3.11+
- pip
- OpenAI API Key

### Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY`: Your OpenAI API key for intent classification.

Optional variables:
- `DATABASE_URL`: (Optional) For persisting conversation memory.

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fintech-ai-router
```

2. Install dependencies:
```bash
pip install -e .
```

### Running the Server

```bash
python -m src.main
```

The server will start on `http://localhost:8000`

### Health Check

```bash
curl http://localhost:8000/health
```



### Query Endpoint

**POST** `/api/v1/query`

Accepts JSON payload:
```json
{
  "query": "Analyze my portfolio health",
  "conversation_id": "optional-conversation-id",
  "portfolio": [
    {"symbol": "AAPL", "shares": 10},
    {"symbol": "GOOGL", "shares": 5}
  ]
}
```

Returns SSE stream with events:
- `safety_check` - Safety validation status
- `safety_rejected` - If query blocked
- `safety_passed` - If query approved
- `classification` - Intent classification status
- `classified` - Classification results
- `routing` - Agent routing status
- `agent_response` - Final agent response
- `error` - Error events

### Example SSE Response

```
event: safety_check
data: {"status": "checking"}

event: safety_passed
data: {"status": "safe"}

event: classified
data: {"intent": "analyze_portfolio", "agent": "portfolio_health"}

event: agent_response
data: {"agent": "portfolio_health", "intent": "analyze_portfolio", "message": "Agent executed successfully", "data": {...}}
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Tests use `unittest.mock.patch` to mock the OpenAI LLM, so they can be run in CI without needing an active `OPENAI_API_KEY`.

## Development

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `execute()` method
3. Register in `Router.agents` dict
4. Add tests in `tests/test_<agent>.py`

## Tradeoffs & Decisions

### Safety Guard Tradeoff
- **Decision**: Implemented a pure Python/Regex rule-based safety guard. Added specific heuristics to bypass blocks for educational queries (e.g. starting with "What is", "Explain").
- **Tradeoff**: While this occasionally risks over-blocking edge cases (or under-blocking cleverly phrased malicious intents), it guarantees sub-10ms latency and purely local execution without external network dependence. 

### LLM Intent Classifier
- **Decision**: Used `gpt-4o-mini` with structured JSON output (Pydantic parsing) in a single call. 
- **Tradeoff**: Lower latency and cost (under $0.05) vs. a more advanced model (`gpt-4.1`). Structured outputs ensure we reliably get the intent, entities, agent, and safety verdict in one pass without parsing errors.




### Pipeline Timeout
- **Decision**: Implemented a 10-second `asyncio.wait_for` timeout around the SSE streaming steps.
- **Reasoning**: Given the target of p95 < 6s, 10s is a sane buffer for network jitters with the OpenAI API. If the LLM takes longer than 10s, we aggressively cut it off and emit an `error` SSE event to prevent hanging connections.





### Empty Portfolio Handling
- **Decision**: Instead of failing or throwing an error, the Portfolio Health agent recognizes empty portfolios and pivots strictly to a `BUILD` recommendation format, encouraging the user to set goals and start diversifying.





## Defence Video
https://youtu.be/oi01tE_VB9E  