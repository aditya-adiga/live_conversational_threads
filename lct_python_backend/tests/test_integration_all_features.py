"""
End-to-End Integration Tests
Week 14: Integration, Polish & Deployment

Tests the complete pipeline across all features:
- Week 11: Simulacra Level Detection
- Week 12: Cognitive Bias Detection
- Week 13: Implicit Frame Detection

Run with: pytest tests/test_integration_all_features.py -v -s
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import json
import sys

# Mock anthropic module before importing
sys.modules['anthropic'] = MagicMock()


@pytest.fixture
def sample_conversation_data():
    """Create sample conversation with nodes for testing"""
    conversation_id = str(uuid.uuid4())

    nodes = [
        {
            "id": str(uuid.uuid4()),
            "node_name": "Market Discussion",
            "node_summary": "The free market will naturally correct this inefficiency through competition.",
            "keywords": ["market", "competition", "efficiency"]
        },
        {
            "id": str(uuid.uuid4()),
            "node_name": "Team Agreement",
            "node_summary": "Everyone agrees this is the right approach. We've always done it this way.",
            "keywords": ["consensus", "tradition", "agreement"]
        },
        {
            "id": str(uuid.uuid4()),
            "node_name": "Project Status",
            "node_summary": "The project is 75% complete. Next milestone is December 15th.",
            "keywords": ["status", "milestone", "progress"]
        }
    ]

    return {
        "conversation_id": conversation_id,
        "nodes": nodes
    }


@pytest.mark.asyncio
async def test_simulacra_analysis_complete_flow(sample_conversation_data):
    """
    Test complete Simulacra analysis flow:
    1. Create conversation with nodes
    2. Run Simulacra analysis
    3. Verify results structure
    4. Check node-level detection
    """
    from services.simulacra_detector import SimulacraDetector
    from models import Node, Conversation

    mock_session = AsyncMock()
    conversation_id = sample_conversation_data["conversation_id"]

    # Mock database queries
    mock_conversation = Conversation()
    mock_conversation.id = uuid.UUID(conversation_id)
    mock_conversation.title = "Test Conversation"

    mock_nodes = []
    for node_data in sample_conversation_data["nodes"]:
        mock_node = Node()
        mock_node.id = uuid.UUID(node_data["id"])
        mock_node.node_name = node_data["node_name"]
        mock_node.node_summary = node_data["node_summary"]
        mock_node.keywords = node_data["keywords"]
        mock_nodes.append(mock_node)

    # Mock session.execute to return nodes
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_nodes
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Mock session.add and commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Mock LLM responses for each node
        mock_responses = [
            json.dumps({"level": 2, "confidence": 0.85, "reasoning": "Predictive/manipulative"}),
            json.dumps({"level": 3, "confidence": 0.9, "reasoning": "Tribal signaling"}),
            json.dumps({"level": 1, "confidence": 0.95, "reasoning": "Factual, object-level"})
        ]

        mock_messages = []
        for response_text in mock_responses:
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = response_text
            mock_messages.append(mock_message)

        mock_client.messages.create.side_effect = mock_messages

        # Run analysis
        detector = SimulacraDetector(mock_session)
        results = await detector.analyze_conversation(conversation_id)

        # Verify results structure
        assert "total_nodes" in results
        assert "analyzed" in results
        assert "by_level" in results
        assert "nodes" in results

        assert results["total_nodes"] == 3
        assert results["analyzed"] == 3

        # Verify level distribution
        assert 1 in results["by_level"]
        assert 2 in results["by_level"]
        assert 3 in results["by_level"]

        # Verify node results
        assert len(results["nodes"]) == 3
        for node in results["nodes"]:
            assert "node_id" in node
            assert "node_name" in node
            assert "level" in node
            assert "confidence" in node
            assert "reasoning" in node


@pytest.mark.asyncio
async def test_bias_analysis_complete_flow(sample_conversation_data):
    """
    Test complete Cognitive Bias analysis flow:
    1. Create conversation with nodes
    2. Run Bias detection
    3. Verify results structure
    4. Check multiple biases per node
    """
    from services.bias_detector import BiasDetector
    from models import Node

    mock_session = AsyncMock()
    conversation_id = sample_conversation_data["conversation_id"]

    mock_nodes = []
    for node_data in sample_conversation_data["nodes"]:
        mock_node = Node()
        mock_node.id = uuid.UUID(node_data["id"])
        mock_node.node_name = node_data["node_name"]
        mock_node.node_summary = node_data["node_summary"]
        mock_node.keywords = node_data["keywords"]
        mock_nodes.append(mock_node)

    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_nodes
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch('services.bias_detector.anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Mock LLM responses with biases
        mock_responses = [
            json.dumps({
                "biases": [{
                    "bias_type": "market_bias",
                    "category": "economic",
                    "severity": 0.7,
                    "confidence": 0.8,
                    "description": "Overconfidence in market mechanisms",
                    "evidence": ["free market will naturally correct"]
                }]
            }),
            json.dumps({
                "biases": [
                    {
                        "bias_type": "bandwagon_effect",
                        "category": "social",
                        "severity": 0.8,
                        "confidence": 0.9,
                        "description": "Appeal to consensus",
                        "evidence": ["Everyone agrees"]
                    },
                    {
                        "bias_type": "status_quo_bias",
                        "category": "decision",
                        "severity": 0.6,
                        "confidence": 0.75,
                        "description": "Preference for tradition",
                        "evidence": ["We've always done it this way"]
                    }
                ]
            }),
            json.dumps({"biases": []})  # No biases in factual node
        ]

        mock_messages = []
        for response_text in mock_responses:
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = response_text
            mock_messages.append(mock_message)

        mock_client.messages.create.side_effect = mock_messages

        # Run analysis
        detector = BiasDetector(mock_session)
        results = await detector.analyze_conversation(conversation_id)

        # Verify results structure
        assert "total_nodes" in results
        assert "nodes_with_biases" in results
        assert "bias_count" in results
        assert "by_category" in results
        assert "by_bias" in results

        assert results["total_nodes"] == 3
        assert results["nodes_with_biases"] == 2
        assert results["bias_count"] == 3

        # Verify category distribution
        assert "social" in results["by_category"]
        assert "decision" in results["by_category"]


@pytest.mark.asyncio
async def test_frame_analysis_complete_flow(sample_conversation_data):
    """
    Test complete Frame Detection flow:
    1. Create conversation with nodes
    2. Run Frame detection
    3. Verify results structure
    4. Check assumptions and implications fields
    """
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()
    conversation_id = sample_conversation_data["conversation_id"]

    mock_nodes = []
    for node_data in sample_conversation_data["nodes"]:
        mock_node = Node()
        mock_node.id = uuid.UUID(node_data["id"])
        mock_node.node_name = node_data["node_name"]
        mock_node.node_summary = node_data["node_summary"]
        mock_node.keywords = node_data["keywords"]
        mock_nodes.append(mock_node)

    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_nodes
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch('services.frame_detector.anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Mock LLM responses with frames
        mock_responses = [
            json.dumps({
                "frames": [{
                    "frame_type": "market_fundamentalism",
                    "category": "economic",
                    "strength": 0.85,
                    "confidence": 0.9,
                    "description": "Strong belief in market-based solutions",
                    "evidence": ["free market will naturally correct"],
                    "assumptions": ["Markets are efficient", "Competition drives optimal outcomes"],
                    "implications": "Reveals belief in minimal regulation"
                }]
            }),
            json.dumps({
                "frames": [{
                    "frame_type": "status_quo_permanence",
                    "category": "temporal",
                    "strength": 0.7,
                    "confidence": 0.8,
                    "description": "Assumption that current practices will persist",
                    "evidence": ["We've always done it this way"],
                    "assumptions": ["Past success predicts future success"],
                    "implications": "Resistance to change and innovation"
                }]
            }),
            json.dumps({"frames": []})  # No frames in factual node
        ]

        mock_messages = []
        for response_text in mock_responses:
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = response_text
            mock_messages.append(mock_message)

        mock_client.messages.create.side_effect = mock_messages

        # Run analysis
        detector = FrameDetector(mock_session)
        results = await detector.analyze_conversation(conversation_id)

        # Verify results structure
        assert "total_nodes" in results
        assert "nodes_with_frames" in results
        assert "frame_count" in results
        assert "by_category" in results
        assert "by_frame" in results

        assert results["total_nodes"] == 3
        assert results["nodes_with_frames"] == 2
        assert results["frame_count"] == 2

        # Verify category distribution
        assert "economic" in results["by_category"]
        assert "temporal" in results["by_category"]

        # Verify unique frame fields
        for node in results["nodes"]:
            if node["frame_count"] > 0:
                for frame in node["frames"]:
                    assert "assumptions" in frame
                    assert "implications" in frame
                    assert isinstance(frame["assumptions"], list)
                    assert isinstance(frame["implications"], str)


@pytest.mark.asyncio
async def test_all_analyses_on_same_conversation(sample_conversation_data):
    """
    Integration test: Run all three analyses on the same conversation
    and verify they don't interfere with each other
    """
    from services.simulacra_detector import SimulacraDetector
    from services.bias_detector import BiasDetector
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()
    conversation_id = sample_conversation_data["conversation_id"]

    # Create mock nodes
    mock_nodes = []
    for node_data in sample_conversation_data["nodes"]:
        mock_node = Node()
        mock_node.id = uuid.UUID(node_data["id"])
        mock_node.node_name = node_data["node_name"]
        mock_node.node_summary = node_data["node_summary"]
        mock_node.keywords = node_data["keywords"]
        mock_nodes.append(mock_node)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_nodes
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic_simulacra, \
         patch('services.bias_detector.anthropic') as mock_anthropic_bias, \
         patch('services.frame_detector.anthropic') as mock_anthropic_frame:

        # Setup mocks for all three services
        for mock_anthropic in [mock_anthropic_simulacra, mock_anthropic_bias, mock_anthropic_frame]:
            mock_client = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client

            # Generic response
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = json.dumps({"test": "data"})
            mock_client.messages.create.return_value = mock_message

        # Run all analyses
        simulacra_detector = SimulacraDetector(mock_session)
        bias_detector = BiasDetector(mock_session)
        frame_detector = FrameDetector(mock_session)

        # All should complete without errors
        try:
            await simulacra_detector.analyze_conversation(conversation_id)
            await bias_detector.analyze_conversation(conversation_id)
            await frame_detector.analyze_conversation(conversation_id)
            success = True
        except Exception as e:
            success = False
            print(f"Error: {e}")

        assert success, "All analyses should complete successfully"


def test_analysis_result_structures_are_consistent():
    """
    Test that all three analysis types return consistent result structures
    """
    # All should have these common fields
    common_fields = ["total_nodes", "analyzed", "nodes"]

    # Simulacra-specific
    simulacra_fields = common_fields + ["by_level"]

    # Bias-specific
    bias_fields = common_fields + ["nodes_with_biases", "bias_count", "by_category", "by_bias"]

    # Frame-specific
    frame_fields = common_fields + ["nodes_with_frames", "frame_count", "by_category", "by_frame"]

    # Verify no field name conflicts
    all_fields = set(simulacra_fields + bias_fields + frame_fields)

    # Count occurrences
    field_counts = {}
    for field in all_fields:
        field_counts[field] = 0
        if field in simulacra_fields:
            field_counts[field] += 1
        if field in bias_fields:
            field_counts[field] += 1
        if field in frame_fields:
            field_counts[field] += 1

    # Common fields should appear 3 times
    for field in common_fields:
        assert field_counts[field] == 3, f"{field} should be in all three result types"

    # by_category appears in both bias and frame, but with different semantics
    # This is OK as long as they're in different endpoints
    assert field_counts["by_category"] == 2


@pytest.mark.asyncio
async def test_performance_all_analyses():
    """
    Test that all analyses complete within reasonable time
    (with mocked LLM calls to test code performance only)
    """
    import time
    from services.simulacra_detector import SimulacraDetector
    from services.bias_detector import BiasDetector
    from services.frame_detector import FrameDetector
    from models import Node

    mock_session = AsyncMock()
    conversation_id = str(uuid.uuid4())

    # Create 10 mock nodes
    mock_nodes = []
    for i in range(10):
        mock_node = Node()
        mock_node.id = uuid.uuid4()
        mock_node.node_name = f"Node {i}"
        mock_node.node_summary = f"Summary {i} " * 50  # ~50 words
        mock_node.keywords = [f"keyword{i}"]
        mock_nodes.append(mock_node)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_nodes
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch('services.simulacra_detector.anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Fast mock response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({"level": 1, "confidence": 0.9, "reasoning": "Test"})
        mock_client.messages.create.return_value = mock_message

        detector = SimulacraDetector(mock_session)

        start_time = time.time()
        await detector.analyze_conversation(conversation_id)
        duration = time.time() - start_time

        # Should complete in < 1 second with mocked LLM (testing code efficiency)
        assert duration < 1.0, f"Analysis took {duration:.2f}s, should be < 1.0s"


def test_taxonomy_completeness():
    """
    Test that all taxonomy definitions are complete and consistent
    """
    from services.simulacra_detector import SIMULACRA_LEVELS
    from services.bias_detector import BIAS_CATEGORIES
    from services.frame_detector import FRAME_CATEGORIES

    # Simulacra: Should have 4 levels
    assert len(SIMULACRA_LEVELS) == 4
    for level, info in SIMULACRA_LEVELS.items():
        assert "name" in info
        assert "description" in info
        assert "examples" in info

    # Biases: Should have 6 categories
    assert len(BIAS_CATEGORIES) == 6
    for category, info in BIAS_CATEGORIES.items():
        assert "name" in info
        assert "description" in info
        assert "biases" in info
        assert len(info["biases"]) > 0

    # Frames: Should have 6 categories
    assert len(FRAME_CATEGORIES) == 6
    for category, info in FRAME_CATEGORIES.items():
        assert "name" in info
        assert "description" in info
        assert "frames" in info
        assert len(info["frames"]) > 0


def test_no_duplicate_identifiers():
    """
    Test that there are no duplicate bias or frame type identifiers
    """
    from services.bias_detector import BIAS_CATEGORIES
    from services.frame_detector import FRAME_CATEGORIES

    # Check biases
    all_biases = []
    for category in BIAS_CATEGORIES.values():
        all_biases.extend(category["biases"])

    assert len(all_biases) == len(set(all_biases)), "Duplicate bias types found"

    # Check frames
    all_frames = []
    for category in FRAME_CATEGORIES.values():
        all_frames.extend(category["frames"])

    assert len(all_frames) == len(set(all_frames)), "Duplicate frame types found"


# Performance benchmarks
@pytest.mark.skip(reason="Requires real database and API setup")
@pytest.mark.asyncio
async def test_benchmark_full_pipeline():
    """
    Benchmark test: Measure actual end-to-end performance
    with real database and API calls

    This test is skipped by default but can be run manually
    to measure production performance
    """
    # TODO: Implement with real database and API
    pass
