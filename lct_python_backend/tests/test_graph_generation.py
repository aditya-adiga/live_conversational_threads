"""
Tests for graph generation service.

Run with: pytest tests/test_graph_generation.py -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from services.graph_generation import GraphGenerationService, PromptLoader
from parsers.google_meet import ParsedTranscript, Utterance


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPromptLoader:
    """Tests for PromptLoader class."""

    def test_load_prompts(self):
        """Test loading prompts from JSON."""
        loader = PromptLoader()

        assert loader.prompts is not None
        assert "prompts" in loader.prompts
        assert "version" in loader.prompts

    def test_get_prompt(self):
        """Test getting a specific prompt."""
        loader = PromptLoader()

        prompt = loader.get_prompt("initial_clustering")

        assert prompt is not None
        assert "description" in prompt
        assert "model" in prompt
        assert "template" in prompt

    def test_get_nonexistent_prompt_raises_error(self):
        """Test that getting non-existent prompt raises KeyError."""
        loader = PromptLoader()

        with pytest.raises(KeyError):
            loader.get_prompt("nonexistent_prompt")

    def test_render_template(self):
        """Test rendering a prompt template."""
        loader = PromptLoader()

        rendered = loader.render_template(
            "initial_clustering",
            utterance_count=10,
            participant_count=3,
            participants="Alice, Bob, Charlie",
            transcript="Test transcript"
        )

        assert "10" in rendered
        assert "3" in rendered
        assert "Alice, Bob, Charlie" in rendered
        assert "Test transcript" in rendered


class TestGraphGenerationService:
    """Tests for GraphGenerationService class."""

    def create_sample_transcript(self) -> ParsedTranscript:
        """Create a sample transcript for testing."""
        utterances = [
            Utterance(
                speaker="Alice",
                text="Let's discuss the project timeline.",
                start_time=0.0,
                end_time=3.0,
                sequence_number=0,
            ),
            Utterance(
                speaker="Bob",
                text="I think we should aim for end of Q1.",
                start_time=3.0,
                end_time=6.0,
                sequence_number=1,
            ),
            Utterance(
                speaker="Charlie",
                text="That sounds reasonable to me.",
                start_time=6.0,
                end_time=9.0,
                sequence_number=2,
            ),
            Utterance(
                speaker="Alice",
                text="Great. Let's also talk about the budget.",
                start_time=9.0,
                end_time=12.0,
                sequence_number=3,
            ),
            Utterance(
                speaker="Bob",
                text="We have $50K allocated for this phase.",
                start_time=12.0,
                end_time=15.0,
                sequence_number=4,
            ),
        ]

        return ParsedTranscript(
            utterances=utterances,
            participants=["Alice", "Bob", "Charlie"],
            duration=15.0,
            parse_metadata={
                "utterance_count": 5,
                "participant_count": 3,
            }
        )

    @pytest.mark.asyncio
    async def test_generate_graph_without_llm(self):
        """Test graph generation without LLM (fallback mode)."""
        service = GraphGenerationService(llm_client=None, db=None)
        transcript = self.create_sample_transcript()

        graph = await service.generate_graph(
            conversation_id="test-123",
            transcript=transcript,
            save_to_db=False,
        )

        assert graph is not None
        assert "nodes" in graph
        assert "edges" in graph
        assert graph["node_count"] > 0
        assert graph["edge_count"] >= 0

    @pytest.mark.asyncio
    async def test_fallback_nodes_creation(self):
        """Test fallback node creation."""
        service = GraphGenerationService(llm_client=None, db=None)
        transcript = self.create_sample_transcript()

        nodes = service._create_fallback_nodes("test-123", transcript)

        assert len(nodes) > 0
        assert all("id" in node for node in nodes)
        assert all("title" in node for node in nodes)
        assert all("zoom_level_visible" in node for node in nodes)

    def test_format_transcript_for_llm(self):
        """Test transcript formatting for LLM."""
        service = GraphGenerationService()
        transcript = self.create_sample_transcript()

        formatted = service._format_transcript_for_llm(transcript)

        assert "Alice:" in formatted
        assert "Bob:" in formatted
        assert "Charlie:" in formatted
        assert "project timeline" in formatted

    def test_create_temporal_edges(self):
        """Test temporal edge creation."""
        service = GraphGenerationService()

        nodes = [
            {"id": "node1", "sequence_number": 0},
            {"id": "node2", "sequence_number": 1},
            {"id": "node3", "sequence_number": 2},
        ]

        edges = service._create_temporal_edges(nodes)

        assert len(edges) == 2  # n-1 edges for n nodes
        assert edges[0]["source_node_id"] == "node1"
        assert edges[0]["target_node_id"] == "node2"
        assert edges[0]["relationship_type"] == "temporal"
        assert edges[1]["source_node_id"] == "node2"
        assert edges[1]["target_node_id"] == "node3"

    def test_temporal_edges_with_single_node(self):
        """Test temporal edges with only one node."""
        service = GraphGenerationService()

        nodes = [{"id": "node1", "sequence_number": 0}]
        edges = service._create_temporal_edges(nodes)

        assert len(edges) == 0

    def test_get_zoom_distribution(self):
        """Test zoom level distribution calculation."""
        service = GraphGenerationService()

        nodes = [
            {"zoom_level_visible": [1, 2, 3]},
            {"zoom_level_visible": [3, 4, 5]},
            {"zoom_level_visible": [3]},
        ]

        distribution = service._get_zoom_distribution(nodes)

        assert distribution[1] == 1
        assert distribution[2] == 1
        assert distribution[3] == 3
        assert distribution[4] == 1
        assert distribution[5] == 1

    def test_detect_relationships_heuristic(self):
        """Test heuristic-based relationship detection."""
        service = GraphGenerationService()

        nodes = [
            {
                "id": "node1",
                "keywords": ["timeline", "deadline", "project"],
                "sequence_number": 0,
            },
            {
                "id": "node2",
                "keywords": ["budget", "cost"],
                "sequence_number": 1,
            },
            {
                "id": "node3",
                "keywords": ["timeline", "project", "schedule"],
                "sequence_number": 2,
            },
        ]

        edges = service._detect_relationships_heuristic(nodes)

        # Should detect relationship between node1 and node3 (shared keywords)
        assert any(
            e["source_node_id"] == "node1" and e["target_node_id"] == "node3"
            for e in edges
        )

    def test_parse_llm_response_json(self):
        """Test parsing clean JSON from LLM."""
        service = GraphGenerationService()

        # Mock response with clean JSON
        class MockResponse:
            class choices:
                class message:
                    content = '[{"title": "Test Node", "summary": "Test"}]'

        response = MockResponse()
        response.choices = [MockResponse.choices]

        nodes = service._parse_llm_response(response)

        assert len(nodes) == 1
        assert nodes[0]["title"] == "Test Node"

    def test_parse_llm_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        service = GraphGenerationService()

        class MockResponse:
            class choices:
                class message:
                    content = '```json\n[{"title": "Test"}]\n```'

        response = MockResponse()
        response.choices = [MockResponse.choices]

        nodes = service._parse_llm_response(response)

        assert len(nodes) == 1
        assert nodes[0]["title"] == "Test"

    def test_create_node_from_data(self):
        """Test creating a node from LLM data."""
        service = GraphGenerationService()
        transcript = self.create_sample_transcript()

        node_data = {
            "title": "Timeline Discussion",
            "summary": "Team discusses project timeline",
            "start_utterance": 0,
            "end_utterance": 2,
            "zoom_levels": [3, 4, 5],
            "primary_speaker": "Alice",
            "keywords": ["timeline", "project", "Q1"],
        }

        node = service._create_node_from_data(
            conversation_id="test-123",
            node_data=node_data,
            transcript=transcript,
            sequence=0,
        )

        assert node["title"] == "Timeline Discussion"
        assert node["summary"] == "Team discusses project timeline"
        assert node["zoom_level_visible"] == [3, 4, 5]
        assert node["speaker_info"]["primary_speaker"] == "Alice"
        assert "timeline" in node["keywords"]


class TestGraphGenerationIntegration:
    """Integration tests for graph generation."""

    @pytest.mark.asyncio
    async def test_full_graph_generation_workflow(self):
        """Test complete graph generation workflow."""
        # Create sample transcript
        utterances = [
            Utterance(speaker="Alice", text=f"Utterance {i}", start_time=i*3.0, end_time=(i+1)*3.0, sequence_number=i)
            for i in range(10)
        ]

        transcript = ParsedTranscript(
            utterances=utterances,
            participants=["Alice"],
            duration=30.0,
        )

        # Generate graph
        service = GraphGenerationService(llm_client=None, db=None)
        graph = await service.generate_graph(
            conversation_id="test-conv",
            transcript=transcript,
            save_to_db=False,
        )

        # Verify structure
        assert graph["conversation_id"] == "test-conv"
        assert graph["node_count"] > 0
        assert len(graph["nodes"]) == graph["node_count"]
        assert len(graph["edges"]) == graph["edge_count"]

        # Verify nodes have required fields
        for node in graph["nodes"]:
            assert "id" in node
            assert "title" in node
            assert "summary" in node
            assert "zoom_level_visible" in node
            assert "utterance_ids" in node

        # Verify edges connect valid nodes
        node_ids = {n["id"] for n in graph["nodes"]}
        for edge in graph["edges"]:
            assert edge["source_node_id"] in node_ids
            assert edge["target_node_id"] in node_ids

    @pytest.mark.asyncio
    async def test_graph_with_real_transcript(self):
        """Test graph generation with real parsed transcript."""
        from parsers import GoogleMeetParser

        parser = GoogleMeetParser()
        transcript_path = FIXTURES_DIR / "sample_transcript_simple.txt"

        transcript = parser.parse_file(str(transcript_path))

        service = GraphGenerationService(llm_client=None, db=None)
        graph = await service.generate_graph(
            conversation_id="real-conv",
            transcript=transcript,
            save_to_db=False,
        )

        assert graph["node_count"] > 0
        assert graph["edge_count"] > 0

        # Check zoom distribution
        distribution = graph["metadata"]["zoom_level_distribution"]
        assert any(count > 0 for count in distribution.values())


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_transcript(self):
        """Test handling of empty transcript."""
        service = GraphGenerationService(llm_client=None, db=None)

        transcript = ParsedTranscript(
            utterances=[],
            participants=[],
            duration=0.0,
        )

        graph = await service.generate_graph(
            conversation_id="empty",
            transcript=transcript,
            save_to_db=False,
        )

        assert graph["node_count"] == 0
        assert graph["edge_count"] == 0

    @pytest.mark.asyncio
    async def test_single_utterance_transcript(self):
        """Test handling of transcript with single utterance."""
        service = GraphGenerationService(llm_client=None, db=None)

        transcript = ParsedTranscript(
            utterances=[
                Utterance(speaker="Alice", text="Hello", start_time=0.0, end_time=1.0, sequence_number=0)
            ],
            participants=["Alice"],
            duration=1.0,
        )

        graph = await service.generate_graph(
            conversation_id="single",
            transcript=transcript,
            save_to_db=False,
        )

        assert graph["node_count"] >= 1
        assert graph["edge_count"] == 0  # No edges with single node

    def test_invalid_node_indices(self):
        """Test handling of invalid utterance indices."""
        service = GraphGenerationService()

        transcript = ParsedTranscript(
            utterances=[
                Utterance(speaker="Alice", text="Test", start_time=0.0, end_time=1.0, sequence_number=0)
            ],
            participants=["Alice"],
            duration=1.0,
        )

        # Node with indices beyond transcript
        node_data = {
            "title": "Test",
            "summary": "Test",
            "start_utterance": 0,
            "end_utterance": 100,  # Beyond transcript
            "zoom_levels": [3],
            "keywords": [],
        }

        node = service._create_node_from_data(
            conversation_id="test",
            node_data=node_data,
            transcript=transcript,
            sequence=0,
        )

        # Should clamp to valid range
        assert len(node["utterance_ids"]) <= len(transcript.utterances)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
