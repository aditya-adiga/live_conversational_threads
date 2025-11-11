"""
Tests for instrumentation decorators and tracking.

Run with: pytest tests/test_instrumentation.py -v
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from instrumentation.decorators import (
    track_api_call,
    APICallTracker,
    get_tracker,
)


class MockUsage:
    """Mock usage object for OpenAI-style responses."""

    def __init__(self, prompt_tokens=100, completion_tokens=50):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class MockResponse:
    """Mock LLM API response."""

    def __init__(self, model="gpt-4", usage=None):
        self.model = model
        self.usage = usage or MockUsage()


class TestAPICallTracker:
    """Tests for APICallTracker class."""

    def test_tracker_initialization(self):
        """Test tracker initializes correctly."""
        tracker = APICallTracker()

        assert tracker.db is None
        assert tracker.call_logs == []

    def test_tracker_with_db_connection(self):
        """Test tracker with database connection."""
        mock_db = Mock()
        tracker = APICallTracker(db_connection=mock_db)

        assert tracker.db is mock_db

    @pytest.mark.asyncio
    async def test_log_api_call_to_memory(self):
        """Test logging API call to memory when no DB."""
        tracker = APICallTracker()

        await tracker.log_api_call(
            call_id="test-123",
            endpoint="test_endpoint",
            conversation_id="conv-123",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.009,
            latency_ms=500,
            timestamp=datetime.now(),
            success=True,
        )

        assert len(tracker.call_logs) == 1
        log = tracker.call_logs[0]

        assert log["endpoint"] == "test_endpoint"
        assert log["model"] == "gpt-4"
        assert log["total_tokens"] == 150
        assert log["cost_usd"] == 0.009

    def test_get_in_memory_logs(self):
        """Test retrieving in-memory logs."""
        tracker = APICallTracker()
        tracker.call_logs = [{"test": "log1"}, {"test": "log2"}]

        logs = tracker.get_in_memory_logs()

        assert len(logs) == 2
        assert logs[0]["test"] == "log1"


class TestTrackAPICallDecorator:
    """Tests for @track_api_call decorator."""

    @pytest.mark.asyncio
    async def test_decorator_logs_successful_call(self):
        """Test decorator logs successful API call."""
        # Clear any existing logs
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_endpoint")
        async def mock_llm_call(conversation_id: str):
            return MockResponse(model="gpt-4", usage=MockUsage(100, 50))

        result = await mock_llm_call(conversation_id="test-123")

        # Check result is returned correctly
        assert result.model == "gpt-4"

        # Check log was created
        logs = tracker.get_in_memory_logs()
        assert len(logs) > 0

        # Find our log entry
        log = next((l for l in logs if l.get("endpoint") == "test_endpoint"), None)
        assert log is not None
        assert log["success"] is True
        assert log["model"] == "gpt-4"
        assert log["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_decorator_logs_failed_call(self):
        """Test decorator logs failed API call."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_endpoint_fail")
        async def mock_llm_call_that_fails(conversation_id: str):
            raise ValueError("API call failed")

        with pytest.raises(ValueError, match="API call failed"):
            await mock_llm_call_that_fails(conversation_id="test-123")

        # Check failure was logged
        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_endpoint_fail"), None)

        assert log is not None
        assert log["success"] is False
        assert "API call failed" in log["error_message"]

    @pytest.mark.asyncio
    async def test_decorator_extracts_conversation_id_from_kwargs(self):
        """Test decorator extracts conversation_id from kwargs."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_endpoint_kwargs")
        async def mock_llm_call(text: str, conversation_id: str = None):
            return MockResponse()

        await mock_llm_call(text="test", conversation_id="conv-456")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_endpoint_kwargs"), None)

        assert log is not None
        assert log["conversation_id"] == "conv-456"

    @pytest.mark.asyncio
    async def test_decorator_measures_latency(self):
        """Test decorator measures call latency."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_endpoint_latency")
        async def mock_slow_llm_call(conversation_id: str):
            await asyncio.sleep(0.1)  # Simulate 100ms delay
            return MockResponse()

        await mock_slow_llm_call(conversation_id="test-123")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_endpoint_latency"), None)

        assert log is not None
        assert log["latency_ms"] >= 100  # Should be at least 100ms

    @pytest.mark.asyncio
    async def test_decorator_handles_anthropic_response_format(self):
        """Test decorator handles Anthropic-style responses."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        class AnthropicUsage:
            def __init__(self):
                self.input_tokens = 200
                self.output_tokens = 100

        class AnthropicResponse:
            def __init__(self):
                self.model = "claude-3-sonnet-20240229"
                self.usage = AnthropicUsage()
                self.content = "response text"

        @track_api_call("test_anthropic")
        async def mock_anthropic_call(conversation_id: str):
            return AnthropicResponse()

        result = await mock_anthropic_call(conversation_id="test-123")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_anthropic"), None)

        assert log is not None
        assert log["model"] == "claude-3-sonnet-20240229"
        assert log["total_tokens"] == 300

    @pytest.mark.asyncio
    async def test_decorator_handles_dict_response_format(self):
        """Test decorator handles dictionary response format."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_dict_response")
        async def mock_dict_response_call(conversation_id: str):
            return {
                "model": "gpt-3.5-turbo",
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 25,
                },
            }

        result = await mock_dict_response_call(conversation_id="test-123")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_dict_response"), None)

        assert log is not None
        assert log["model"] == "gpt-3.5-turbo"
        assert log["total_tokens"] == 75

    def test_decorator_on_sync_function(self):
        """Test decorator works on synchronous functions."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_sync")
        def mock_sync_llm_call(conversation_id: str):
            return MockResponse(model="gpt-4", usage=MockUsage(100, 50))

        result = mock_sync_llm_call(conversation_id="test-123")

        assert result.model == "gpt-4"

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_sync"), None)

        assert log is not None
        assert log["model"] == "gpt-4"


class TestCostCalculationIntegration:
    """Tests for cost calculation integration with tracker."""

    @pytest.mark.asyncio
    async def test_cost_calculated_correctly(self):
        """Test that cost is calculated and logged correctly."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        @track_api_call("test_cost_calc")
        async def mock_llm_call(conversation_id: str):
            # GPT-4: $0.03/1K input, $0.06/1K output
            # 1000 input + 500 output = $0.03 + $0.03 = $0.06
            return MockResponse(model="gpt-4", usage=MockUsage(1000, 500))

        await mock_llm_call(conversation_id="test-123")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_cost_calc"), None)

        assert log is not None
        # Cost should be approximately $0.06
        assert abs(log["cost_usd"] - 0.06) < 0.001

    @pytest.mark.asyncio
    async def test_cost_calculated_for_claude(self):
        """Test cost calculation for Claude models."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        class ClaudeUsage:
            input_tokens = 1000
            output_tokens = 1000

        class ClaudeResponse:
            model = "claude-3-sonnet-20240229"
            usage = ClaudeUsage()

        @track_api_call("test_claude_cost")
        async def mock_claude_call(conversation_id: str):
            return ClaudeResponse()

        await mock_claude_call(conversation_id="test-123")

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_claude_cost"), None)

        assert log is not None
        # Claude Sonnet: $0.003/1K input, $0.015/1K output
        # 1000 input + 1000 output = $0.003 + $0.015 = $0.018
        assert abs(log["cost_usd"] - 0.018) < 0.001


class TestCustomConversationIDExtractor:
    """Tests for custom conversation_id extraction."""

    @pytest.mark.asyncio
    async def test_custom_extractor(self):
        """Test using custom conversation_id extractor."""
        tracker = get_tracker()
        tracker.call_logs.clear()

        def extract_id(*args, **kwargs):
            # Extract from first arg which is an object
            return args[0].id if args else None

        class Request:
            def __init__(self, req_id):
                self.id = req_id

        @track_api_call("test_custom_extractor", extract_conversation_id=extract_id)
        async def mock_llm_call(request: Request):
            return MockResponse()

        await mock_llm_call(Request("custom-id-789"))

        logs = tracker.get_in_memory_logs()
        log = next((l for l in logs if l.get("endpoint") == "test_custom_extractor"), None)

        assert log is not None
        assert log["conversation_id"] == "custom-id-789"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
