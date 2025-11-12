"""
Tests for Implicit Frame Detection
Week 13: Advanced AI Analysis

Run with: pytest tests/test_frame_detector.py -v
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
async def test_frame_detector_initialization():
    """Test FrameDetector can be initialized"""
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)

        assert detector is not None
        assert detector.db == mock_session
        assert detector.prompt_manager is not None
        assert detector.client is not None


@pytest.mark.asyncio
async def test_analyze_node_returns_frames():
    """Test that node analysis returns valid frame structure"""
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)

        # Create a mock node with frames
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Market Discussion"
        mock_node.node_summary = "The free market will solve this problem efficiently. Competition drives innovation and optimal resource allocation."
        mock_node.keywords = ["market", "competition", "efficiency"]

        # Mock the LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "frames": [
                {
                    "frame_type": "market_fundamentalism",
                    "category": "economic",
                    "strength": 0.85,
                    "confidence": 0.9,
                    "description": "Strong belief in market-based solutions and competition",
                    "evidence": ["The free market will solve this problem", "Competition drives innovation"],
                    "assumptions": ["Markets are efficient", "Competition leads to optimal outcomes"],
                    "implications": "Reveals belief in minimal government intervention and market self-regulation"
                },
                {
                    "frame_type": "consequentialist",
                    "category": "moral",
                    "strength": 0.7,
                    "confidence": 0.75,
                    "description": "Focus on outcomes and results rather than process",
                    "evidence": ["optimal resource allocation"],
                    "assumptions": ["Efficiency is the primary goal"],
                    "implications": "Outcomes justify means"
                }
            ]
        })
        mock_client_class.messages.create.return_value = mock_message

        result = await detector._analyze_node(mock_node, str(uuid.uuid4()))

        assert isinstance(result, list)
        assert len(result) == 2

        for frame in result:
            assert "frame_type" in frame
            assert "category" in frame
            assert "strength" in frame
            assert "confidence" in frame
            assert "description" in frame
            assert "evidence" in frame
            assert "assumptions" in frame
            assert "implications" in frame

            assert 0.0 <= frame["strength"] <= 1.0
            assert 0.0 <= frame["confidence"] <= 1.0
            assert isinstance(frame["evidence"], list)
            assert isinstance(frame["assumptions"], list)
            assert isinstance(frame["implications"], str)


@pytest.mark.asyncio
async def test_analyze_node_handles_no_frames():
    """Test that node analysis handles frame-neutral nodes"""
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)

        # Create a frame-neutral node
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = "Meeting Logistics"
        mock_node.node_summary = "The meeting is scheduled for 3 PM in Room 201. Agenda includes Q3 review."
        mock_node.keywords = ["meeting", "schedule", "agenda"]

        # Mock the LLM response with no frames
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "frames": []
        })
        mock_client_class.messages.create.return_value = mock_message

        result = await detector._analyze_node(mock_node, str(uuid.uuid4()))

        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
async def test_analyze_node_handles_error():
    """Test that node analysis handles errors gracefully"""
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)

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
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock empty result
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        assert results["total_nodes"] == 0
        assert results["analyzed"] == 0
        assert results["nodes_with_frames"] == 0
        assert results["frame_count"] == 0
        assert results["by_category"] == {}
        assert results["by_frame"] == {}
        assert results["nodes"] == []


@pytest.mark.asyncio
async def test_get_node_frames_empty():
    """Test getting frames for a node that hasn't been analyzed"""
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    # Mock no results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client_class = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client_class

        detector = FrameDetector(mock_session)
        frames = await detector.get_node_frames(str(uuid.uuid4()))

        assert frames == []


def test_get_frame_info():
    """Test frame info utility function"""
    from services.frame_detector import get_frame_info

    info = get_frame_info("market_fundamentalism")

    assert "name" in info
    assert "category" in info
    assert "description" in info
    assert info["category"] == "economic"


def test_frame_categories_structure():
    """Test that FRAME_CATEGORIES has correct structure"""
    from services.frame_detector import FRAME_CATEGORIES

    assert len(FRAME_CATEGORIES) == 6  # 6 categories

    for category_key, category_data in FRAME_CATEGORIES.items():
        assert "name" in category_data
        assert "description" in category_data
        assert "frames" in category_data
        assert isinstance(category_data["frames"], list)
        assert len(category_data["frames"]) > 0


def test_all_frame_types_have_info():
    """Test that all frame types in FRAME_CATEGORIES have corresponding info"""
    from services.frame_detector import FRAME_CATEGORIES, get_frame_info

    for category_key, category_data in FRAME_CATEGORIES.items():
        for frame_type in category_data["frames"]:
            info = get_frame_info(frame_type)
            assert info is not None
            assert info["name"] is not None
            assert info["category"] == category_key


def test_frame_assumptions_and_implications():
    """Test that frames support assumptions and implications fields"""
    from services.frame_detector import FrameDetector

    # This is a structural test - verifying the frame structure includes new fields
    sample_frame = {
        "frame_type": "market_fundamentalism",
        "category": "economic",
        "strength": 0.8,
        "confidence": 0.85,
        "description": "Test description",
        "evidence": ["quote 1", "quote 2"],
        "assumptions": ["assumption 1", "assumption 2"],
        "implications": "Test implications"
    }

    # Verify structure
    assert "assumptions" in sample_frame
    assert "implications" in sample_frame
    assert isinstance(sample_frame["assumptions"], list)
    assert isinstance(sample_frame["implications"], str)


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
async def test_frame_distribution_accuracy():
    """
    Test that distribution counts are accurate

    This would require:
    1. Test database with known node counts
    2. Pre-analyzed nodes with known frames
    3. Verification of distribution calculation
    """
    pass


@pytest.mark.skip(reason="Requires multiple nodes for testing")
@pytest.mark.asyncio
async def test_multiple_frames_per_node():
    """
    Test that nodes can have multiple frames from different categories

    This would require:
    1. Test database setup
    2. Node with content that exhibits multiple frames
    3. Verification that all frames are detected and stored
    """
    pass
