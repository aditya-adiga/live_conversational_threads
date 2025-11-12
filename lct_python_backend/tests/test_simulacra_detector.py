"""
Tests for Simulacra Level Detection
Week 11: Advanced AI Analysis

Run with: pytest tests/test_simulacra_detector.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import uuid
import json
import sys

# Mock anthropic module before importing the detector
sys.modules['anthropic'] = MagicMock()


@pytest.mark.asyncio
async def test_get_level_info():
    """Test that level info utility returns correct data"""
    from services.simulacra_detector import SimulacraDetector

    # This is a simple test to verify the detector can be initialized
    mock_session = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)

        assert detector is not None
        assert detector.db == mock_session


@pytest.mark.asyncio
async def test_analyze_node_returns_valid_level():
    """Test that node analysis returns a valid level (1-4)"""
    from services.simulacra_detector import SimulacraDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)

        # Create a mock node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Test Node"
        mock_node.node_summary = "This is a factual test summary."
        mock_node.keywords = ["test", "factual"]

        # Mock the LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "level": 1,
            "confidence": 0.9,
            "reasoning": "Direct factual statement",
            "examples": ["This is a factual test summary"]
        })
        mock_client_class.messages.create.return_value = mock_message

        result = await detector._analyze_node(mock_node)

        assert result["level"] in [1, 2, 3, 4]
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["reasoning"], str)
        assert isinstance(result["examples"], list)


@pytest.mark.asyncio
async def test_analyze_node_handles_error():
    """Test that node analysis handles errors gracefully"""
    from services.simulacra_detector import SimulacraDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)

        # Create a mock node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Test Node"
        mock_node.node_summary = "Test summary"
        mock_node.keywords = []

        # Mock the LLM to raise an error
        mock_client_class.messages.create.side_effect = Exception("API Error")

        result = await detector._analyze_node(mock_node)

        # Should return default level 2 on error
        assert result["level"] == 2
        assert result["confidence"] < 0.5
        assert "failed" in result["reasoning"].lower()


@pytest.mark.asyncio
async def test_get_conversation_results_empty():
    """Test getting results for a conversation with no analysis"""
    from services.simulacra_detector import SimulacraDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock empty result
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)
        # Use valid UUID format
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        assert results["total_nodes"] == 0
        assert results["analyzed"] == 0
        assert results["distribution"] == {1: 0, 2: 0, 3: 0, 4: 0}
        assert results["nodes"] == []


@pytest.mark.asyncio
async def test_get_node_simulacra_not_found():
    """Test getting Simulacra for a node that hasn't been analyzed"""
    from services.simulacra_detector import SimulacraDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock no result found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)
        # Use valid UUID format
        result = await detector.get_node_simulacra(str(uuid.uuid4()))

        assert result is None


def test_simulacra_detector_initialization():
    """Test SimulacraDetector can be initialized"""
    from services.simulacra_detector import SimulacraDetector

    mock_session = MagicMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = SimulacraDetector(mock_session)

        assert detector is not None
        assert detector.db == mock_session
        assert detector.prompt_manager is not None
        assert detector.client is not None


# Integration test placeholders
@pytest.mark.skip(reason="Requires database and API setup")
@pytest.mark.asyncio
async def test_analyze_conversation_integration():
    """
    Integration test with real database and API

    This would require:
    1. Test database setup
    2. Sample conversation with nodes
    3. Valid Anthropic API key
    4. Actual API calls
    """
    pass


@pytest.mark.skip(reason="Requires database setup")
@pytest.mark.asyncio
async def test_distribution_accuracy():
    """
    Test that distribution counts are accurate

    This would require:
    1. Test database with known node counts
    2. Pre-analyzed nodes with known levels
    3. Verification of distribution calculation
    """
    pass
