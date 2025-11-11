"""
Decorators for automatic API call tracking and cost logging.

Usage:
    @track_api_call("generate_clusters")
    async def generate_clusters(conversation_id: str, utterances: List[Utterance]):
        response = await openai.ChatCompletion.create(...)
        return response
"""

import time
import asyncio
from functools import wraps
from typing import Callable, Any, Optional, Dict
from datetime import datetime
import uuid

from .cost_calculator import calculate_cost, calculate_cost_breakdown


class APICallTracker:
    """
    Tracks API calls and logs them to the database.

    This class provides the core functionality for the @track_api_call decorator.
    """

    def __init__(self, db_connection=None):
        """
        Initialize the tracker with a database connection.

        Args:
            db_connection: Database connection/pool (optional)
        """
        self.db = db_connection
        self.call_logs = []  # In-memory buffer if DB not available

    async def log_api_call(
        self,
        call_id: str,
        endpoint: str,
        conversation_id: Optional[str],
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_usd: float,
        latency_ms: int,
        timestamp: datetime,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an API call to the database.

        Args:
            call_id: Unique identifier for this API call
            endpoint: Name of the endpoint/function making the call
            conversation_id: Associated conversation ID (if applicable)
            model: Model used (e.g., "gpt-4", "claude-3-sonnet")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total tokens (input + output)
            cost_usd: Cost in USD
            latency_ms: Request latency in milliseconds
            timestamp: Timestamp of the call
            success: Whether the call succeeded
            error_message: Error message if call failed
            metadata: Additional metadata (temperature, max_tokens, etc.)
        """
        log_entry = {
            "id": call_id,
            "endpoint": endpoint,
            "conversation_id": conversation_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "timestamp": timestamp,
            "success": success,
            "error_message": error_message,
            "metadata": metadata or {},
        }

        if self.db:
            try:
                # Log to database using SQLAlchemy
                from models import APICallLog
                from sqlalchemy.ext.asyncio import AsyncSession

                if isinstance(self.db, AsyncSession):
                    api_log = APICallLog(
                        id=uuid.UUID(call_id) if isinstance(call_id, str) else call_id,
                        endpoint=endpoint,
                        conversation_id=uuid.UUID(conversation_id) if conversation_id and isinstance(conversation_id, str) else conversation_id,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost_usd=cost_usd,
                        latency_ms=latency_ms,
                        timestamp=timestamp,
                        success=success,
                        error_message=error_message,
                        metadata=metadata,
                    )
                    self.db.add(api_log)
                    await self.db.commit()
            except Exception as e:
                print(f"Failed to log API call to database: {e}")
                # Fall back to in-memory logging
                self.call_logs.append(log_entry)
        else:
            # No database connection, store in memory
            self.call_logs.append(log_entry)

    def get_in_memory_logs(self):
        """Get in-memory logs (for testing or when DB unavailable)."""
        return self.call_logs


# Global tracker instance
_global_tracker = APICallTracker()


def set_db_connection(db):
    """Set the database connection for the global tracker."""
    _global_tracker.db = db


def get_tracker() -> APICallTracker:
    """Get the global tracker instance."""
    return _global_tracker


def track_api_call(
    endpoint_name: str,
    extract_conversation_id: Optional[Callable] = None,
):
    """
    Decorator to track cost and performance of LLM API calls.

    This decorator automatically:
    1. Measures call latency
    2. Extracts token counts from response
    3. Calculates cost based on model pricing
    4. Logs to api_calls_log table
    5. Handles errors gracefully

    Args:
        endpoint_name: Name of the endpoint/feature (e.g., "generate_clusters")
        extract_conversation_id: Optional function to extract conversation_id from args/kwargs

    Returns:
        Decorated function

    Example:
        @track_api_call("generate_clusters")
        async def generate_clusters(conversation_id: str, utterances: List[Utterance]):
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[...],
            )
            return response

        # The decorator will automatically log the call with cost and metrics
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            call_id = str(uuid.uuid4())
            start_time = time.time()
            timestamp = datetime.now()

            # Extract conversation_id if extractor provided
            conversation_id = None
            if extract_conversation_id:
                conversation_id = extract_conversation_id(*args, **kwargs)
            elif "conversation_id" in kwargs:
                conversation_id = kwargs["conversation_id"]
            elif len(args) > 0 and hasattr(args[0], "conversation_id"):
                conversation_id = args[0].conversation_id

            try:
                # Execute the function
                response = await func(*args, **kwargs)

                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)

                # Extract token usage and model from response
                # Support both OpenAI and Anthropic response formats
                model = None
                input_tokens = 0
                output_tokens = 0
                metadata = {}

                # OpenAI format
                if hasattr(response, "model"):
                    model = response.model

                if hasattr(response, "usage"):
                    usage = response.usage
                    # Try OpenAI format first
                    if hasattr(usage, "prompt_tokens"):
                        input_tokens = usage.prompt_tokens
                    # Fallback to Anthropic format
                    elif hasattr(usage, "input_tokens"):
                        input_tokens = usage.input_tokens

                    # Try OpenAI format first
                    if hasattr(usage, "completion_tokens"):
                        output_tokens = usage.completion_tokens
                    # Fallback to Anthropic format
                    elif hasattr(usage, "output_tokens"):
                        output_tokens = usage.output_tokens

                # Dictionary format (for custom wrappers)
                elif isinstance(response, dict):
                    model = response.get("model")
                    usage = response.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
                    output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))

                total_tokens = input_tokens + output_tokens

                # Calculate cost
                cost_usd = 0.0
                if model and total_tokens > 0:
                    try:
                        cost_usd = calculate_cost(model, input_tokens, output_tokens)
                    except ValueError as e:
                        print(f"Warning: Could not calculate cost for model '{model}': {e}")

                # Extract additional metadata
                if hasattr(response, "choices") and len(response.choices) > 0:
                    metadata["finish_reason"] = getattr(response.choices[0], "finish_reason", None)

                # Log the API call
                await _global_tracker.log_api_call(
                    call_id=call_id,
                    endpoint=endpoint_name,
                    conversation_id=conversation_id,
                    model=model or "unknown",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    timestamp=timestamp,
                    success=True,
                    metadata=metadata,
                )

                return response

            except Exception as e:
                # Log failure
                latency_ms = int((time.time() - start_time) * 1000)

                await _global_tracker.log_api_call(
                    call_id=call_id,
                    endpoint=endpoint_name,
                    conversation_id=conversation_id,
                    model="unknown",
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                    timestamp=timestamp,
                    success=False,
                    error_message=str(e),
                )

                # Re-raise the exception
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            """Synchronous wrapper for non-async functions."""
            call_id = str(uuid.uuid4())
            start_time = time.time()
            timestamp = datetime.now()

            conversation_id = None
            if extract_conversation_id:
                conversation_id = extract_conversation_id(*args, **kwargs)
            elif "conversation_id" in kwargs:
                conversation_id = kwargs["conversation_id"]

            try:
                response = func(*args, **kwargs)
                latency_ms = int((time.time() - start_time) * 1000)

                # Extract usage (same logic as async)
                model = getattr(response, "model", "unknown")
                usage = getattr(response, "usage", None)

                input_tokens = 0
                output_tokens = 0

                if usage:
                    input_tokens = getattr(usage, "prompt_tokens", getattr(usage, "input_tokens", 0))
                    output_tokens = getattr(usage, "completion_tokens", getattr(usage, "output_tokens", 0))

                total_tokens = input_tokens + output_tokens

                cost_usd = 0.0
                if model and total_tokens > 0:
                    try:
                        cost_usd = calculate_cost(model, input_tokens, output_tokens)
                    except ValueError:
                        pass

                # For sync functions, we need to handle logging differently
                # Store in memory buffer and log later
                log_entry = {
                    "call_id": call_id,
                    "endpoint": endpoint_name,
                    "conversation_id": conversation_id,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "timestamp": timestamp,
                    "success": True,
                }
                _global_tracker.call_logs.append(log_entry)

                return response

            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)

                log_entry = {
                    "call_id": call_id,
                    "endpoint": endpoint_name,
                    "conversation_id": conversation_id,
                    "model": "unknown",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "latency_ms": latency_ms,
                    "timestamp": timestamp,
                    "success": False,
                    "error_message": str(e),
                }
                _global_tracker.call_logs.append(log_entry)

                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
