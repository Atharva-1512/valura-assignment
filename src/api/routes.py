import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from src.models import QueryRequest, SafetyResult, ClassifierResult, AgentResponse
from src.core.safety import SafetyGuard
from src.core.classifier import IntentClassifier
from src.core.router import Router

logger = logging.getLogger(__name__)

router = APIRouter()
safety_guard = SafetyGuard()
classifier = IntentClassifier()
agent_router = Router()

conversation_store = {}  # In-memory persistence for conversation memory

PIPELINE_TIMEOUT_SECONDS = 10.0  # Sane timeout: P95 is <6s, 10s gives buffer for network jitter without hanging


@router.post("/query")
async def query_endpoint(request: QueryRequest) -> EventSourceResponse:
    """Main query endpoint with SSE streaming."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async def run_pipeline():
                # Step 1: Safety Guard (fast, local)
                yield _create_event("safety_check", {"status": "checking"})
                safety_result = safety_guard.check_query(request.query)

                if not safety_result.safe:
                    yield _create_event("safety_rejected", {
                        "category": safety_result.category,
                        "message": safety_result.message
                    })
                    return

                yield _create_event("safety_passed", {"status": "safe"})

                # Step 2: Intent Classification
                yield _create_event("classification", {"status": "classifying"})
                classifier_result = await asyncio.to_thread(
                    classifier.classify, request.query, None
                )

                yield _create_event("classified", {
                    "intent": classifier_result.intent,
                    "agent": classifier_result.agent
                })

                # Step 3: Routing and Execution
                yield _create_event("routing", {"agent": classifier_result.agent})
                agent_response = await asyncio.to_thread(
                    agent_router.route, classifier_result, request.portfolio
                )

                yield _create_event("agent_response", agent_response.model_dump())

            # We can't wrap a generator directly in wait_for, so we collect events
            # But SSE is meant to stream as they happen.
            # Instead of wait_for around the whole generator, we wait_for around each step or an async task queue.
            # A simple way for SSE is to run the generation in a background task and stream its results with timeout.
            
            queue = asyncio.Queue()
            
            async def producer():
                try:
                    # In-memory persistence retrieval
                    memory_obj = {"history": []}
                    if request.conversation_id:
                        memory_obj = conversation_store.get(request.conversation_id, {"history": []})
                
                    # Step 1: Safety Guard
                    await queue.put(_create_event("safety_check", {"status": "checking"}))
                    safety_result = await asyncio.to_thread(safety_guard.check_query, request.query)

                    if not safety_result.safe:
                        await queue.put(_create_event("safety_rejected", {
                            "category": safety_result.category,
                            "message": safety_result.message
                        }))
                        await queue.put(None)  # Signal end
                        return

                    await queue.put(_create_event("safety_passed", {"status": "safe"}))

                    # Step 2: Intent Classification
                    await queue.put(_create_event("classification", {"status": "classifying"}))
                    classifier_result = await asyncio.to_thread(
                        classifier.classify, request.query, memory_obj
                    )

                    await queue.put(_create_event("classified", {
                        "intent": classifier_result.intent,
                        "agent": classifier_result.agent
                    }))

                    # Step 3: Routing and Execution
                    await queue.put(_create_event("routing", {"agent": classifier_result.agent}))
                    agent_response = await asyncio.to_thread(
                        agent_router.route, classifier_result, request.portfolio
                    )
                    
                    # Update Memory
                    if request.conversation_id:
                        memory_obj["history"].append({"role": "user", "content": request.query})
                        memory_obj["history"].append({"role": "assistant", "content": json.dumps(agent_response.model_dump())})
                        conversation_store[request.conversation_id] = memory_obj

                    await queue.put(_create_event("agent_response", agent_response.model_dump()))
                    await queue.put(None)  # Signal end
                except Exception as e:
                    logger.error(f"Pipeline error: {e}")
                    await queue.put(_create_event("error", {"message": str(e)}))
                    await queue.put(None)

            producer_task = asyncio.create_task(producer())
            
            while True:
                # Wait for the next event with a timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=PIPELINE_TIMEOUT_SECONDS)
                    if event is None:
                        break
                    yield event
                except asyncio.TimeoutError:
                    yield _create_event("error", {"message": "Request timed out"})
                    producer_task.cancel()
                    break

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield _create_event("error", {"message": str(e)})

    return EventSourceResponse(event_generator())


def _create_event(event_type: str, data: dict) -> str:
    """Create SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"