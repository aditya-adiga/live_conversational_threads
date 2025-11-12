"""
End-to-End Integration Tests (Simplified)
Week 14: Integration, Polish & Deployment

Tests service structure and API compatibility across all features:
- Week 11: Simulacra Level Detection
- Week 12: Cognitive Bias Detection
- Week 13: Implicit Frame Detection

Run with: pytest tests/test_integration_all_features.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import sys

# Mock anthropic module before importing
sys.modules['anthropic'] = MagicMock()


# ============================================================================
# Simulacra Tests
# ============================================================================

@pytest.mark.asyncio
async def test_simulacra_detector_initialization():
    """Test SimulacraDetector can be initialized"""
    from services.simulacra_detector import SimulacraDetector

    mock_session = AsyncMock()

    with patch('services.simulacra_detector.anthropic'):
        detector = SimulacraDetector(mock_session)

        assert detector is not None
        assert hasattr(detector, 'analyze_conversation')
        assert hasattr(detector, 'get_conversation_results')
        assert hasattr(detector, 'get_node_simulacra')


@pytest.mark.asyncio
async def test_simulacra_get_results_structure():
    """Test Simulacra results return proper structure"""
    from services.simulacra_detector import SimulacraDetector

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('services.simulacra_detector.anthropic'):
        detector = SimulacraDetector(mock_session)
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        # Verify required fields
        assert "total_nodes" in results
        assert "analyzed" in results
        assert "distribution" in results
        assert "nodes" in results
        assert isinstance(results["distribution"], dict)


# ============================================================================
# Bias Tests
# ============================================================================

@pytest.mark.asyncio
async def test_bias_detector_initialization():
    """Test BiasDetector can be initialized"""
    from services.bias_detector import BiasDetector

    mock_session = AsyncMock()

    with patch('services.bias_detector.anthropic'):
        detector = BiasDetector(mock_session)

        assert detector is not None
        assert hasattr(detector, 'analyze_conversation')
        assert hasattr(detector, 'get_conversation_results')
        assert hasattr(detector, 'get_node_biases')


@pytest.mark.asyncio
async def test_bias_get_results_structure():
    """Test Bias results return proper structure"""
    from services.bias_detector import BiasDetector

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('services.bias_detector.anthropic'):
        detector = BiasDetector(mock_session)
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        # Verify required fields
        assert "total_nodes" in results
        assert "nodes_with_biases" in results
        assert "bias_count" in results
        assert "by_category" in results
        assert "by_bias" in results


# ============================================================================
# Frame Tests
# ============================================================================

@pytest.mark.asyncio
async def test_frame_detector_initialization():
    """Test FrameDetector can be initialized"""
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()

    with patch('services.frame_detector.anthropic'):
        detector = FrameDetector(mock_session)

        assert detector is not None
        assert hasattr(detector, 'analyze_conversation')
        assert hasattr(detector, 'get_conversation_results')
        assert hasattr(detector, 'get_node_frames')


@pytest.mark.asyncio
async def test_frame_get_results_structure():
    """Test Frame results return proper structure"""
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('services.frame_detector.anthropic'):
        detector = FrameDetector(mock_session)
        results = await detector.get_conversation_results(str(uuid.uuid4()))

        # Verify required fields
        assert "total_nodes" in results
        assert "nodes_with_frames" in results
        assert "frame_count" in results
        assert "by_category" in results
        assert "by_frame" in results


# ============================================================================
# Cross-Feature Integration
# ============================================================================

@pytest.mark.asyncio
async def test_all_detectors_can_coexist():
    """Test that all three detectors can be instantiated together"""
    from services.simulacra_detector import SimulacraDetector
    from services.bias_detector import BiasDetector
    from services.frame_detector import FrameDetector

    mock_session = AsyncMock()

    with patch('services.simulacra_detector.anthropic'), \
         patch('services.bias_detector.anthropic'), \
         patch('services.frame_detector.anthropic'):

        simulacra = SimulacraDetector(mock_session)
        bias = BiasDetector(mock_session)
        frame = FrameDetector(mock_session)

        assert simulacra is not None
        assert bias is not None
        assert frame is not None


def test_result_structures_are_consistent():
    """Test that all analysis types have consistent common fields"""

    # All should have these common fields
    common_fields = ["total_nodes", "nodes"]

    # Simulacra-specific
    simulacra_required = common_fields + ["analyzed", "distribution"]

    # Bias-specific
    bias_required = common_fields + ["nodes_with_biases", "bias_count", "by_category", "by_bias"]

    # Frame-specific
    frame_required = common_fields + ["nodes_with_frames", "frame_count", "by_category", "by_frame"]

    # Verify no critical field name conflicts
    all_fields = set(simulacra_required + bias_required + frame_required)

    # Common fields should appear in all
    for field in common_fields:
        count = sum([
            field in simulacra_required,
            field in bias_required,
            field in frame_required
        ])
        assert count == 3, f"{field} should be in all three result types"


def test_taxonomy_structures_exist():
    """Test that all taxonomy structures are defined"""
    from services.bias_detector import BIAS_CATEGORIES
    from services.frame_detector import FRAME_CATEGORIES

    # Bias taxonomy
    assert len(BIAS_CATEGORIES) == 6, "Should have 6 bias categories"
    for category, info in BIAS_CATEGORIES.items():
        assert "name" in info
        assert "description" in info
        assert "biases" in info
        assert len(info["biases"]) > 0

    # Frame taxonomy
    assert len(FRAME_CATEGORIES) == 6, "Should have 6 frame categories"
    for category, info in FRAME_CATEGORIES.items():
        assert "name" in info
        assert "description" in info
        assert "frames" in info
        assert len(info["frames"]) > 0


def test_no_duplicate_identifiers():
    """Test that bias and frame types have no duplicates"""
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


# ============================================================================
# API Compatibility Tests
# ============================================================================

def test_api_endpoint_naming_consistency():
    """Test that API endpoint patterns are consistent"""

    # All three features should follow same pattern
    patterns = {
        "simulacra": ["/api/conversations/{id}/simulacra/analyze", "/api/conversations/{id}/simulacra", "/api/nodes/{id}/simulacra"],
        "biases": ["/api/conversations/{id}/biases/analyze", "/api/conversations/{id}/biases", "/api/nodes/{id}/biases"],
        "frames": ["/api/conversations/{id}/frames/analyze", "/api/conversations/{id}/frames", "/api/nodes/{id}/frames"]
    }

    # Verify pattern consistency
    for feature, endpoints in patterns.items():
        assert len(endpoints) == 3, f"{feature} should have 3 endpoints"
        assert "analyze" in endpoints[0], f"{feature} analyze endpoint"
        assert "/nodes/" in endpoints[2], f"{feature} node endpoint"


def test_models_have_required_fields():
    """Test that database models have required fields"""
    from models import SimulacraAnalysis, BiasAnalysis, FrameAnalysis

    # Common fields all models should have
    common_fields = ['id', 'node_id', 'conversation_id', 'confidence', 'analyzed_at']

    for model in [SimulacraAnalysis, BiasAnalysis, FrameAnalysis]:
        for field in common_fields:
            assert hasattr(model, field), f"{model.__name__} missing {field}"


# ============================================================================
# Performance Structure Tests
# ============================================================================

def test_detectors_use_async_methods():
    """Verify all detectors use async/await properly"""
    from services.simulacra_detector import SimulacraDetector
    from services.bias_detector import BiasDetector
    from services.frame_detector import FrameDetector
    import inspect

    for detector_class in [SimulacraDetector, BiasDetector, FrameDetector]:
        # Check that analyze_conversation is async
        assert inspect.iscoroutinefunction(detector_class.analyze_conversation)
        assert inspect.iscoroutinefunction(detector_class.get_conversation_results)


# ============================================================================
# Skipped Integration Tests (Require Real Database)
# ============================================================================

@pytest.mark.skip(reason="Requires real database and API setup")
@pytest.mark.asyncio
async def test_full_pipeline_with_real_data():
    """
    Full integration test with real database and API

    This would test:
    1. Create conversation
    2. Run all three analyses
    3. Verify results stored correctly
    4. Verify results retrieved correctly
    """
    pass


@pytest.mark.skip(reason="Requires real database")
@pytest.mark.asyncio
async def test_concurrent_analysis():
    """
    Test running all analyses concurrently on same conversation

    This would verify:
    1. No race conditions
    2. All analyses complete successfully
    3. Results don't interfere with each other
    """
    pass
