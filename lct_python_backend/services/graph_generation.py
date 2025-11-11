"""
Graph generation service for Live Conversational Threads.

Uses LLMs to analyze transcripts and generate hierarchical node structures
with temporal and contextual edges across 5 zoom levels.
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

from instrumentation import track_api_call
from parsers import ParsedTranscript, Utterance as ParserUtterance
from models import Node, Relationship, Conversation


class PromptLoader:
    """Loads and manages prompts from prompts.json."""

    def __init__(self, prompts_file: str = "prompts.json"):
        """
        Initialize prompt loader.

        Args:
            prompts_file: Path to prompts.json file
        """
        self.prompts_file = prompts_file
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """Load prompts from JSON file."""
        prompts_path = Path(__file__).parent.parent / self.prompts_file

        if not prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {prompts_path}")

        with open(prompts_path, 'r') as f:
            return json.load(f)

    def get_prompt(self, prompt_name: str) -> Dict:
        """
        Get a prompt configuration by name.

        Args:
            prompt_name: Name of the prompt (e.g., "initial_clustering")

        Returns:
            Prompt configuration dict

        Raises:
            KeyError: If prompt not found
        """
        if prompt_name not in self.prompts.get("prompts", {}):
            raise KeyError(f"Prompt '{prompt_name}' not found in prompts.json")

        return self.prompts["prompts"][prompt_name]

    def render_template(self, prompt_name: str, **kwargs) -> str:
        """
        Render a prompt template with variables.

        Args:
            prompt_name: Name of the prompt
            **kwargs: Template variables

        Returns:
            Rendered prompt text
        """
        prompt = self.get_prompt(prompt_name)
        template = prompt.get("template", "")

        return template.format(**kwargs)


class GraphGenerationService:
    """
    Service for generating conversation graphs using LLM analysis.

    This service:
    1. Takes a parsed transcript
    2. Uses LLMs to identify topic clusters at 5 zoom levels
    3. Creates nodes and edges
    4. Assigns zoom levels for multi-scale visualization
    5. Saves to database
    """

    def __init__(self, llm_client=None, db=None):
        """
        Initialize graph generation service.

        Args:
            llm_client: LLM client (OpenAI, Anthropic, etc.)
            db: Database session
        """
        self.llm_client = llm_client
        self.db = db
        self.prompt_loader = PromptLoader()

    async def generate_graph(
        self,
        conversation_id: str,
        transcript: ParsedTranscript,
        save_to_db: bool = True,
    ) -> Dict:
        """
        Generate complete conversation graph from transcript.

        Args:
            conversation_id: UUID of conversation
            transcript: ParsedTranscript from parser
            save_to_db: Whether to save to database

        Returns:
            Dict with nodes, edges, and metadata
        """
        # Step 1: Generate nodes using LLM clustering
        nodes = await self._generate_nodes(conversation_id, transcript)

        # Step 2: Create temporal edges (sequential connections)
        temporal_edges = self._create_temporal_edges(nodes)

        # Step 3: Detect contextual relationships
        contextual_edges = await self._detect_contextual_relationships(nodes)

        # Combine edges
        all_edges = temporal_edges + contextual_edges

        # Save to database if requested
        if save_to_db and self.db:
            await self._save_graph_to_db(conversation_id, nodes, all_edges)

        return {
            "conversation_id": conversation_id,
            "nodes": nodes,
            "edges": all_edges,
            "node_count": len(nodes),
            "edge_count": len(all_edges),
            "metadata": {
                "temporal_edges": len(temporal_edges),
                "contextual_edges": len(contextual_edges),
                "zoom_level_distribution": self._get_zoom_distribution(nodes),
            }
        }

    @track_api_call("generate_initial_nodes")
    async def _generate_nodes(
        self,
        conversation_id: str,
        transcript: ParsedTranscript,
    ) -> List[Dict]:
        """
        Generate nodes from transcript using LLM clustering.

        Args:
            conversation_id: UUID of conversation
            transcript: ParsedTranscript

        Returns:
            List of node dicts
        """
        # Format transcript for LLM
        transcript_text = self._format_transcript_for_llm(transcript)

        # Render prompt
        prompt_text = self.prompt_loader.render_template(
            "initial_clustering",
            utterance_count=len(transcript.utterances),
            participant_count=len(transcript.participants),
            participants=", ".join(transcript.participants),
            transcript=transcript_text,
        )

        # Get prompt config
        prompt_config = self.prompt_loader.get_prompt("initial_clustering")

        # Call LLM
        if self.llm_client is None:
            # Fallback: create simple nodes without LLM
            return self._create_fallback_nodes(conversation_id, transcript)

        try:
            # Make LLM API call (this will be tracked by decorator)
            response = await self._call_llm(
                prompt=prompt_text,
                model=prompt_config.get("model", "gpt-4"),
                temperature=prompt_config.get("temperature", 0.5),
                max_tokens=prompt_config.get("max_tokens", 4000),
            )

            # Parse response
            nodes_data = self._parse_llm_response(response)

            # Convert to node dicts with full metadata
            nodes = []
            for i, node_data in enumerate(nodes_data):
                node = self._create_node_from_data(
                    conversation_id=conversation_id,
                    node_data=node_data,
                    transcript=transcript,
                    sequence=i,
                )
                nodes.append(node)

            return nodes

        except Exception as e:
            print(f"Error generating nodes with LLM: {e}")
            # Fallback to simple node generation
            return self._create_fallback_nodes(conversation_id, transcript)

    async def _call_llm(
        self,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.5,
        max_tokens: int = 4000,
    ):
        """
        Call LLM API (abstracted to support different providers).

        Args:
            prompt: Prompt text
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens to generate

        Returns:
            LLM response
        """
        if self.llm_client is None:
            raise ValueError("LLM client not configured")

        # This is a placeholder - actual implementation depends on LLM provider
        # For now, assume OpenAI-compatible interface
        try:
            # Try OpenAI
            response = await self.llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a conversation analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response

        except AttributeError:
            # Try Anthropic
            response = await self.llm_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return response

    def _format_transcript_for_llm(self, transcript: ParsedTranscript) -> str:
        """
        Format transcript for LLM consumption.

        Args:
            transcript: ParsedTranscript

        Returns:
            Formatted text
        """
        lines = []

        for i, utt in enumerate(transcript.utterances):
            time_marker = f"[{utt.start_time:.1f}s]" if utt.start_time else f"[{i}]"
            lines.append(f"{time_marker} {utt.speaker}: {utt.text}")

        return "\n".join(lines)

    def _parse_llm_response(self, response) -> List[Dict]:
        """
        Parse LLM response to extract nodes.

        Args:
            response: LLM API response

        Returns:
            List of node data dicts
        """
        # Extract text from response (handles both OpenAI and Anthropic)
        if hasattr(response, 'choices'):
            # OpenAI format
            text = response.choices[0].message.content
        elif hasattr(response, 'content'):
            # Anthropic format
            if isinstance(response.content, list):
                text = response.content[0].text
            else:
                text = response.content
        else:
            text = str(response)

        # Parse JSON (handle markdown code blocks)
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            nodes_data = json.loads(text)
            if not isinstance(nodes_data, list):
                nodes_data = [nodes_data]
            return nodes_data
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response text: {text[:500]}")
            return []

    def _create_node_from_data(
        self,
        conversation_id: str,
        node_data: Dict,
        transcript: ParsedTranscript,
        sequence: int,
    ) -> Dict:
        """
        Create a full node dict from LLM-generated data.

        Args:
            conversation_id: Conversation UUID
            node_data: Raw node data from LLM
            transcript: Original transcript
            sequence: Sequence number

        Returns:
            Complete node dict
        """
        node_id = str(uuid.uuid4())

        # Extract utterances for this node
        start_idx = node_data.get("start_utterance", 0)
        end_idx = node_data.get("end_utterance", len(transcript.utterances) - 1)

        # Ensure indices are valid
        start_idx = max(0, min(start_idx, len(transcript.utterances) - 1))
        end_idx = max(start_idx, min(end_idx, len(transcript.utterances) - 1))

        node_utterances = transcript.utterances[start_idx:end_idx + 1]

        # Calculate time range
        start_time = node_utterances[0].start_time if node_utterances else 0.0
        end_time = node_utterances[-1].end_time if node_utterances else 0.0

        # Get zoom levels (default to [3] if not specified)
        zoom_levels = node_data.get("zoom_levels", [3])
        if not isinstance(zoom_levels, list):
            zoom_levels = [zoom_levels]

        # Build node
        node = {
            "id": node_id,
            "conversation_id": conversation_id,
            "title": node_data.get("title", f"Segment {sequence + 1}"),
            "summary": node_data.get("summary", ""),
            "node_type": "topic",
            "level": min(zoom_levels) if zoom_levels else 3,
            "zoom_level_visible": zoom_levels,
            "utterance_ids": [start_idx + i for i in range(len(node_utterances))],
            "start_time": start_time,
            "end_time": end_time,
            "sequence_number": sequence,
            "speaker_info": {
                "primary_speaker": node_data.get("primary_speaker"),
                "speakers": list(set(u.speaker for u in node_utterances)),
            },
            "keywords": node_data.get("keywords", []),
            "metadata": {
                "utterance_count": len(node_utterances),
                "generated_by": "llm_clustering",
            }
        }

        return node

    def _create_fallback_nodes(
        self,
        conversation_id: str,
        transcript: ParsedTranscript,
    ) -> List[Dict]:
        """
        Create simple nodes without LLM (fallback).

        Creates basic topic segments every ~5-10 utterances.

        Args:
            conversation_id: Conversation UUID
            transcript: ParsedTranscript

        Returns:
            List of basic node dicts
        """
        nodes = []
        utterances_per_node = 8
        total_utterances = len(transcript.utterances)

        for i in range(0, total_utterances, utterances_per_node):
            start_idx = i
            end_idx = min(i + utterances_per_node - 1, total_utterances - 1)

            node_utterances = transcript.utterances[start_idx:end_idx + 1]

            node_id = str(uuid.uuid4())

            # Get primary speaker (most utterances)
            speaker_counts = {}
            for utt in node_utterances:
                speaker_counts[utt.speaker] = speaker_counts.get(utt.speaker, 0) + 1
            primary_speaker = max(speaker_counts, key=speaker_counts.get) if speaker_counts else None

            node = {
                "id": node_id,
                "conversation_id": conversation_id,
                "title": f"Segment {len(nodes) + 1}",
                "summary": f"Conversation segment with {len(node_utterances)} utterances",
                "node_type": "topic",
                "level": 3,
                "zoom_level_visible": [3, 4, 5],
                "utterance_ids": list(range(start_idx, end_idx + 1)),
                "start_time": node_utterances[0].start_time if node_utterances[0].start_time else 0.0,
                "end_time": node_utterances[-1].end_time if node_utterances[-1].end_time else 0.0,
                "sequence_number": len(nodes),
                "speaker_info": {
                    "primary_speaker": primary_speaker,
                    "speakers": list(set(u.speaker for u in node_utterances)),
                },
                "keywords": [],
                "metadata": {
                    "utterance_count": len(node_utterances),
                    "generated_by": "fallback",
                }
            }

            nodes.append(node)

        return nodes

    def _create_temporal_edges(self, nodes: List[Dict]) -> List[Dict]:
        """
        Create temporal (sequential) edges between nodes.

        Args:
            nodes: List of node dicts

        Returns:
            List of edge dicts
        """
        edges = []

        # Sort nodes by sequence
        sorted_nodes = sorted(nodes, key=lambda n: n.get("sequence_number", 0))

        # Create edges between consecutive nodes
        for i in range(len(sorted_nodes) - 1):
            source = sorted_nodes[i]
            target = sorted_nodes[i + 1]

            edge = {
                "id": str(uuid.uuid4()),
                "source_node_id": source["id"],
                "target_node_id": target["id"],
                "relationship_type": "temporal",
                "strength": 1.0,
                "metadata": {
                    "description": "Sequential conversation flow",
                    "is_temporal": True,
                }
            }

            edges.append(edge)

        return edges

    @track_api_call("detect_contextual_relationships")
    async def _detect_contextual_relationships(
        self,
        nodes: List[Dict],
    ) -> List[Dict]:
        """
        Detect contextual/thematic relationships between nodes using LLM.

        Args:
            nodes: List of node dicts

        Returns:
            List of contextual edge dicts
        """
        if len(nodes) < 2:
            return []

        if self.llm_client is None:
            # Without LLM, use simple heuristics
            return self._detect_relationships_heuristic(nodes)

        try:
            # Format nodes for LLM
            nodes_json = json.dumps([{
                "id": n["id"],
                "title": n["title"],
                "summary": n["summary"],
                "keywords": n.get("keywords", []),
                "sequence": n.get("sequence_number", 0),
            } for n in nodes], indent=2)

            # Render prompt
            prompt_text = self.prompt_loader.render_template(
                "detect_contextual_relationships",
                nodes_json=nodes_json,
            )

            # Get prompt config
            prompt_config = self.prompt_loader.get_prompt("detect_contextual_relationships")

            # Call LLM
            response = await self._call_llm(
                prompt=prompt_text,
                model=prompt_config.get("model", "gpt-4"),
                temperature=prompt_config.get("temperature", 0.3),
                max_tokens=prompt_config.get("max_tokens", 2000),
            )

            # Parse relationships
            relationships_data = self._parse_llm_response(response)

            # Convert to edge dicts
            edges = []
            for rel_data in relationships_data:
                edge = {
                    "id": str(uuid.uuid4()),
                    "source_node_id": rel_data.get("source_node_id"),
                    "target_node_id": rel_data.get("target_node_id"),
                    "relationship_type": rel_data.get("relationship_type", "theme"),
                    "strength": rel_data.get("strength", 0.5),
                    "metadata": {
                        "description": rel_data.get("description", ""),
                        "is_temporal": False,
                    }
                }
                edges.append(edge)

            return edges

        except Exception as e:
            print(f"Error detecting contextual relationships: {e}")
            return self._detect_relationships_heuristic(nodes)

    def _detect_relationships_heuristic(self, nodes: List[Dict]) -> List[Dict]:
        """
        Simple heuristic-based relationship detection (fallback).

        Looks for keyword overlaps between nodes.

        Args:
            nodes: List of node dicts

        Returns:
            List of edge dicts
        """
        edges = []

        for i, source in enumerate(nodes):
            source_keywords = set(source.get("keywords", []))

            if not source_keywords:
                continue

            for target in nodes[i + 2:]:  # Skip adjacent (already have temporal edge)
                target_keywords = set(target.get("keywords", []))

                if not target_keywords:
                    continue

                # Check keyword overlap
                overlap = source_keywords & target_keywords
                if len(overlap) >= 2:
                    strength = len(overlap) / max(len(source_keywords), len(target_keywords))

                    edge = {
                        "id": str(uuid.uuid4()),
                        "source_node_id": source["id"],
                        "target_node_id": target["id"],
                        "relationship_type": "theme",
                        "strength": min(strength, 1.0),
                        "metadata": {
                            "description": f"Shared keywords: {', '.join(overlap)}",
                            "is_temporal": False,
                            "shared_keywords": list(overlap),
                        }
                    }
                    edges.append(edge)

        return edges

    def _get_zoom_distribution(self, nodes: List[Dict]) -> Dict[int, int]:
        """
        Get distribution of nodes across zoom levels.

        Args:
            nodes: List of node dicts

        Returns:
            Dict mapping zoom level to count
        """
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for node in nodes:
            for level in node.get("zoom_level_visible", []):
                if 1 <= level <= 5:
                    distribution[level] += 1

        return distribution

    async def _save_graph_to_db(
        self,
        conversation_id: str,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> None:
        """
        Save generated graph to database.

        Args:
            conversation_id: Conversation UUID
            nodes: List of node dicts
            edges: List of edge dicts
        """
        if self.db is None:
            return

        from sqlalchemy.ext.asyncio import AsyncSession

        if not isinstance(self.db, AsyncSession):
            return

        try:
            # Save nodes
            for node_data in nodes:
                db_node = Node(
                    id=uuid.UUID(node_data["id"]),
                    conversation_id=uuid.UUID(conversation_id),
                    title=node_data["title"],
                    summary=node_data["summary"],
                    node_type=node_data.get("node_type", "topic"),
                    level=node_data.get("level", 3),
                    zoom_level_visible=node_data.get("zoom_level_visible", [3]),
                    utterance_ids=node_data.get("utterance_ids", []),
                    start_time=node_data.get("start_time"),
                    end_time=node_data.get("end_time"),
                    sequence_number=node_data.get("sequence_number", 0),
                    speaker_info=node_data.get("speaker_info", {}),
                    keywords=node_data.get("keywords", []),
                    metadata=node_data.get("metadata", {}),
                )
                self.db.add(db_node)

            # Save edges
            for edge_data in edges:
                db_edge = Relationship(
                    id=uuid.UUID(edge_data["id"]),
                    source_node_id=uuid.UUID(edge_data["source_node_id"]),
                    target_node_id=uuid.UUID(edge_data["target_node_id"]),
                    relationship_type=edge_data.get("relationship_type", "temporal"),
                    strength=edge_data.get("strength", 1.0),
                    metadata=edge_data.get("metadata", {}),
                )
                self.db.add(db_edge)

            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to save graph to database: {e}")
