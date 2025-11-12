"""
Speaker Analytics Service
Calculates comprehensive speaker statistics and role detection
Week 8 implementation
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import statistics

from models import Conversation, Utterance, Node


class SpeakerAnalytics:
    """
    Comprehensive speaker analytics for conversations

    Calculates:
    - Time spoken per speaker
    - Turn count and distribution
    - Topics dominated by each speaker
    - Role detection (facilitator, contributor, observer)
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def calculate_full_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """
        Calculate all speaker analytics for a conversation

        Returns comprehensive analytics including:
        - speakers: Dict of speaker stats
        - timeline: Chronological speaker activity
        - roles: Detected speaker roles
        - summary: Overall conversation statistics
        """
        # Fetch all data
        conversation = await self._get_conversation(conversation_id)
        utterances = await self._get_utterances(conversation_id)
        nodes = await self._get_nodes(conversation_id)

        if not utterances:
            return {
                "speakers": {},
                "timeline": [],
                "roles": {},
                "summary": {
                    "total_duration": 0,
                    "total_turns": 0,
                    "total_speakers": 0
                }
            }

        # Calculate individual metrics
        time_spoken = self.calculate_time_spoken(utterances)
        turn_distribution = self.calculate_turn_distribution(utterances)
        topic_dominance = self.calculate_topic_dominance(nodes, utterances)
        roles = self.detect_speaker_roles(utterances, nodes, time_spoken, turn_distribution)
        timeline = self.calculate_speaker_timeline(utterances)

        # Build speaker profiles
        speakers = {}
        all_speakers = set(time_spoken.keys()) | set(turn_distribution.keys())

        for speaker_id in all_speakers:
            speakers[speaker_id] = {
                "speaker_id": speaker_id,
                "speaker_name": self._get_speaker_name(speaker_id, utterances),
                "time_spoken_seconds": time_spoken.get(speaker_id, 0),
                "time_spoken_percentage": self._calculate_percentage(
                    time_spoken.get(speaker_id, 0),
                    sum(time_spoken.values())
                ),
                "turn_count": turn_distribution.get(speaker_id, 0),
                "turn_percentage": self._calculate_percentage(
                    turn_distribution.get(speaker_id, 0),
                    sum(turn_distribution.values())
                ),
                "topics_dominated": topic_dominance.get(speaker_id, []),
                "role": roles.get(speaker_id, "contributor"),
                "avg_turn_duration": self._calculate_avg_turn_duration(speaker_id, utterances)
            }

        # Summary statistics
        total_duration = conversation.duration_seconds if conversation.duration_seconds else sum(time_spoken.values())

        summary = {
            "conversation_id": str(conversation_id),
            "conversation_name": conversation.conversation_name if conversation else "Unknown",
            "total_duration": total_duration,
            "total_turns": sum(turn_distribution.values()),
            "total_speakers": len(all_speakers),
            "started_at": conversation.started_at.isoformat() if conversation and conversation.started_at else None,
            "ended_at": conversation.ended_at.isoformat() if conversation and conversation.ended_at else None
        }

        return {
            "speakers": speakers,
            "timeline": timeline,
            "roles": roles,
            "summary": summary
        }

    def calculate_time_spoken(self, utterances: List[Utterance]) -> Dict[str, float]:
        """
        Calculate total seconds spoken per speaker

        Args:
            utterances: List of conversation utterances

        Returns:
            Dict mapping speaker_id to total seconds spoken
        """
        time_by_speaker = defaultdict(float)

        for utterance in utterances:
            if utterance.duration_seconds:
                time_by_speaker[utterance.speaker_id] += utterance.duration_seconds
            elif utterance.timestamp_start is not None and utterance.timestamp_end is not None:
                duration = utterance.timestamp_end - utterance.timestamp_start
                time_by_speaker[utterance.speaker_id] += duration
            else:
                # Estimate: ~150 words per minute, average 5 chars per word
                words = len(utterance.text.split())
                estimated_duration = (words / 150.0) * 60.0
                time_by_speaker[utterance.speaker_id] += estimated_duration

        return dict(time_by_speaker)

    def calculate_turn_distribution(self, utterances: List[Utterance]) -> Dict[str, int]:
        """
        Count number of turns (utterances) per speaker

        Args:
            utterances: List of conversation utterances

        Returns:
            Dict mapping speaker_id to turn count
        """
        return dict(Counter(u.speaker_id for u in utterances))

    def calculate_topic_dominance(self, nodes: List[Node], utterances: List[Utterance]) -> Dict[str, List[str]]:
        """
        Identify which topics each speaker dominated

        A speaker dominates a topic if they contributed >40% of utterances in that node

        Args:
            nodes: List of conversation nodes
            utterances: List of conversation utterances

        Returns:
            Dict mapping speaker_id to list of dominated topic names
        """
        # Build utterance lookup
        utterance_map = {str(u.id): u for u in utterances}

        topic_dominance = defaultdict(list)

        for node in nodes:
            if not node.utterance_ids:
                continue

            # Count utterances per speaker in this node
            speaker_counts = defaultdict(int)
            total_utterances = 0

            for utt_id in node.utterance_ids:
                utt_id_str = str(utt_id)
                if utt_id_str in utterance_map:
                    utterance = utterance_map[utt_id_str]
                    speaker_counts[utterance.speaker_id] += 1
                    total_utterances += 1

            # Determine dominance (>40% threshold)
            if total_utterances > 0:
                for speaker_id, count in speaker_counts.items():
                    percentage = count / total_utterances
                    if percentage > 0.4:
                        topic_dominance[speaker_id].append(node.node_name)

        return dict(topic_dominance)

    def detect_speaker_roles(
        self,
        utterances: List[Utterance],
        nodes: List[Node],
        time_spoken: Dict[str, float],
        turn_distribution: Dict[str, int]
    ) -> Dict[str, str]:
        """
        Classify speakers into roles: facilitator, contributor, observer

        Role detection heuristics:
        - Facilitator: Speaks frequently but briefly, distributed across topics
        - Contributor: Speaks extensively, dominates specific topics
        - Observer: Speaks infrequently, short turns

        Args:
            utterances: List of conversation utterances
            nodes: List of conversation nodes
            time_spoken: Time spoken per speaker
            turn_distribution: Turn count per speaker

        Returns:
            Dict mapping speaker_id to role
        """
        roles = {}

        if not utterances:
            return roles

        total_time = sum(time_spoken.values())
        total_turns = sum(turn_distribution.values())

        # Calculate metrics for each speaker
        for speaker_id in set(time_spoken.keys()) | set(turn_distribution.keys()):
            speaker_time = time_spoken.get(speaker_id, 0)
            speaker_turns = turn_distribution.get(speaker_id, 0)

            # Calculate percentages
            time_percentage = speaker_time / total_time if total_time > 0 else 0
            turn_percentage = speaker_turns / total_turns if total_turns > 0 else 0

            # Average turn duration
            avg_turn_duration = speaker_time / speaker_turns if speaker_turns > 0 else 0

            # Count topics where this speaker appears
            topics_count = sum(
                1 for node in nodes
                if node.utterance_ids and any(
                    str(utt_id) in [str(u.id) for u in utterances if u.speaker_id == speaker_id]
                    for utt_id in node.utterance_ids
                )
            )

            # Role classification logic
            if turn_percentage > 0.3 and avg_turn_duration < 10:
                # Many short turns = facilitator
                roles[speaker_id] = "facilitator"
            elif time_percentage > 0.25 and avg_turn_duration > 15:
                # Significant time with longer turns = contributor
                roles[speaker_id] = "contributor"
            elif turn_percentage < 0.1:
                # Few turns = observer
                roles[speaker_id] = "observer"
            else:
                # Default
                roles[speaker_id] = "contributor"

        return roles

    def calculate_speaker_timeline(self, utterances: List[Utterance]) -> List[Dict[str, Any]]:
        """
        Create chronological timeline of speaker activity

        Returns list of timeline segments with speaker and duration

        Args:
            utterances: List of conversation utterances

        Returns:
            List of timeline segments
        """
        if not utterances:
            return []

        # Sort by sequence number
        sorted_utterances = sorted(utterances, key=lambda u: u.sequence_number)

        timeline = []
        for i, utterance in enumerate(sorted_utterances):
            segment = {
                "sequence_number": utterance.sequence_number,
                "speaker_id": utterance.speaker_id,
                "speaker_name": utterance.speaker_name or utterance.speaker_id,
                "timestamp_start": utterance.timestamp_start,
                "timestamp_end": utterance.timestamp_end,
                "duration_seconds": utterance.duration_seconds or 0,
                "text_preview": utterance.text[:100] + "..." if len(utterance.text) > 100 else utterance.text,
                "is_speaker_change": i == 0 or sorted_utterances[i-1].speaker_id != utterance.speaker_id
            }
            timeline.append(segment)

        return timeline

    # Helper methods

    async def _get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Fetch conversation by ID"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_utterances(self, conversation_id: str) -> List[Utterance]:
        """Fetch all utterances for conversation, ordered by sequence"""
        result = await self.db.execute(
            select(Utterance)
            .where(Utterance.conversation_id == conversation_id)
            .order_by(Utterance.sequence_number)
        )
        return list(result.scalars().all())

    async def _get_nodes(self, conversation_id: str) -> List[Node]:
        """Fetch all nodes for conversation"""
        result = await self.db.execute(
            select(Node).where(Node.conversation_id == conversation_id)
        )
        return list(result.scalars().all())

    def _get_speaker_name(self, speaker_id: str, utterances: List[Utterance]) -> str:
        """Get display name for speaker"""
        for utterance in utterances:
            if utterance.speaker_id == speaker_id and utterance.speaker_name:
                return utterance.speaker_name
        return speaker_id

    def _calculate_percentage(self, value: float, total: float) -> float:
        """Calculate percentage with safe division"""
        if total == 0:
            return 0.0
        return round((value / total) * 100, 2)

    def _calculate_avg_turn_duration(self, speaker_id: str, utterances: List[Utterance]) -> float:
        """Calculate average turn duration for speaker"""
        speaker_utterances = [u for u in utterances if u.speaker_id == speaker_id]
        if not speaker_utterances:
            return 0.0

        durations = []
        for u in speaker_utterances:
            if u.duration_seconds:
                durations.append(u.duration_seconds)
            elif u.timestamp_start is not None and u.timestamp_end is not None:
                durations.append(u.timestamp_end - u.timestamp_start)

        if not durations:
            return 0.0

        return round(statistics.mean(durations), 2)
