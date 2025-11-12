"""
Tests for Cognitive Bias Detection
Week 12: Advanced AI Analysis

Run with: pytest tests/test_bias_detector.py -v
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
async def test_bias_detector_initialization():
    """Test BiasDetector can be initialized"""
    from services.bias_detector import BiasDetector

    mock_session = AsyncMock()

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)

        assert detector is not None
        assert detector.db == mock_session
        assert detector.prompt_manager is not None
        assert detector.client is not None


@pytest.mark.asyncio
async def test_analyze_node_returns_biases():
    """Test that node analysis returns valid bias structure"""
    from services.bias_detector import BiasDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)

        # Create a mock node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Test Node"
        mock_node.node_summary = "Everyone knows this is the best approach. We've always done it this way."
        mock_node.keywords = ["consensus", "tradition"]

        # Mock the LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "biases": [
                {
                    "bias_type": "bandwagon_effect",
                    "category": "social",
                    "severity": 0.7,
                    "confidence": 0.85,
                    "description": "Appealing to consensus ('everyone knows') without evidence",
                    "evidence": ["Everyone knows this is the best approach"]
                },
                {
                    "bias_type": "status_quo_bias",
                    "category": "decision",
                    "severity": 0.6,
                    "confidence": 0.8,
                    "description": "Preferring current practices based solely on tradition",
                    "evidence": ["We've always done it this way"]
                }
            ]
        })
        mock_client_class.messages.create.return_value = mock_message

        result = await detector._analyze_node(mock_node, str(uuid.uuid4()))

        assert isinstance(result, list)
        assert len(result) == 2

        for bias in result:
            assert "bias_type" in bias
            assert "category" in bias
            assert "severity" in bias
            assert "confidence" in bias
            assert "description" in bias
            assert "evidence" in bias

            assert 0.0 <= bias["severity"] <= 1.0
            assert 0.0 <= bias["confidence"] <= 1.0
            assert isinstance(bias["evidence"], list)


@pytest.mark.asyncio
async def test_analyze_node_handles_no_biases():
    """Test that node analysis handles nodes without biases"""
    from services.bias_detector import BiasDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)

        # Create a factual node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Meeting Summary"
        mock_node.node_summary = "The meeting started at 2 PM with 5 attendees. Q3 revenue was $1.2M."
        mock_node.keywords = ["meeting", "revenue"]

        # Mock the LLM response with no biases
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "biases": []
        })
        mock_client_class.messages.create.return_value = mock_message

        result = await detector._analyze_node(mock_node, str(uuid.uuid4()))

        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
async def test_analyze_node_handles_error():
    """Test that node analysis handles errors gracefully"""
    from services.bias_detector import BiasDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)

        # Create a mock node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Test Node"
        mock_node.node_summary = "Test summary"
        mock_node.keywords = []

        # Mock the LLM to raise an error
        mock_client_class.messages.create.side_effect = Exception("API Error")

        result = await detector._analyze_node(mock_node, str(uuid.uuid4()))

        # Should return empty list on error
        assert result == []


@pytest.mark.asyncio
async def test_get_conversation_results_empty():
    """Test getting results for a conversation with no analysis"""
    from services.bias_detector import BiasDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock empty result
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        assert results["total_nodes"] == 0
        assert results["analyzed"] == 0
        assert results["nodes_with_biases"] == 0
        assert results["bias_count"] == 0
        assert results["by_category"] == {}
        assert results["by_bias"] == {}
        assert results["nodes"] == []


@pytest.mark.asyncio
async def test_get_node_biases_empty():
    """Test getting biases for a node that hasn't been analyzed"""
    from services.bias_detector import BiasDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock no results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = BiasDetector(mock_session)
        biases = await detector.get_node_biases(str(uuid.uuid4()))

        assert biases == []


def test_get_bias_info():
    """Test bias info utility function"""
    from services.bias_detector import get_bias_info

    info = get_bias_info("confirmation_bias")

    assert "name" in info
    assert "category" in info
    assert "description" in info
    assert info["category"] == "confirmation"


def test_bias_categories_structure():
    """Test that BIAS_CATEGORIES has correct structure"""
    from services.bias_detector import BIAS_CATEGORIES

    assert len(BIAS_CATEGORIES) == 6  # 6 categories

    for category_key, category_data in BIAS_CATEGORIES.items():
        assert "name" in category_data
        assert "description" in category_data
        assert "biases" in category_data
        assert isinstance(category_data["biases"], list)
        assert len(category_data["biases"]) > 0


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
async def test_bias_distribution_accuracy():
    """
    Test that distribution counts are accurate

    This would require:
    1. Test database with known node counts
    2. Pre-analyzed nodes with known biases
    3. Verification of distribution calculation
    """
    pass
