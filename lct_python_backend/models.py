"""
SQLAlchemy models for Live Conversational Threads V2
Based on DATA_MODEL_V2.md
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Index, CheckConstraint, ARRAY, BigInteger, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Conversation(Base):
    """Top-level conversation container"""
    __tablename__ = "conversations"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_name = Column(Text, nullable=False)
    conversation_type = Column(Text, nullable=False)  # 'live_audio', 'transcript', 'chat', 'hybrid'

    # Source
    source_type = Column(Text, nullable=False)  # 'audio_stream', 'google_meet', 'slack', etc.
    source_metadata = Column(JSONB)

    # Participants
    participant_count = Column(Integer, default=0)
    participants = Column(ARRAY(JSONB))  # Array of participant objects

    # Temporal
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Goals & Intent
    goals = Column(ARRAY(JSONB))  # Array of goal objects
    goal_progress = Column(JSONB)

    # Storage
    gcs_path = Column(Text)  # Path to full conversation JSON in GCS

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))  # Soft delete

    # Privacy
    owner_id = Column(Text, nullable=False)
    visibility = Column(Text, default='private')  # 'private', 'shared', 'public'
    shared_with = Column(ARRAY(Text))

    # Analytics (cached)
    total_utterances = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    total_nodes = Column(Integer, default=0)
    total_claims = Column(Integer, default=0)

    # Full-text search
    tsv_search = Column(TSVECTOR)

    __table_args__ = (
        CheckConstraint(
            "conversation_type IN ('live_audio', 'transcript', 'chat', 'hybrid')",
            name='valid_conversation_type'
        ),
        CheckConstraint(
            "visibility IN ('private', 'shared', 'public')",
            name='valid_visibility'
        ),
        Index('idx_conversations_owner', 'owner_id'),
        Index('idx_conversations_started', 'started_at'),
        Index('idx_conversations_tsv', 'tsv_search', postgresql_using='gin'),
    )


class Utterance(Base):
    """Atomic unit of speech/text"""
    __tablename__ = "utterances"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)

    # Content
    text = Column(Text, nullable=False)
    text_cleaned = Column(Text)  # Normalized

    # Speaker
    speaker_id = Column(Text, nullable=False)
    speaker_name = Column(Text)
    speaker_role = Column(Text)

    # Temporal
    sequence_number = Column(Integer, nullable=False)
    timestamp_start = Column(Float)
    timestamp_end = Column(Float)
    duration_seconds = Column(Float)

    # Context
    chunk_id = Column(UUID(as_uuid=True))
    node_id = Column(UUID(as_uuid=True))
    thread_id = Column(UUID(as_uuid=True))

    # Metadata
    confidence_score = Column(Float)
    language = Column(Text, default='en')
    emotion = Column(Text)
    energy_level = Column(Float)

    # Source-specific
    platform_metadata = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(timestamp_start IS NULL AND timestamp_end IS NULL) OR "
            "(timestamp_end IS NULL) OR "
            "(timestamp_end >= timestamp_start)",
            name='valid_timestamps'
        ),
        Index('idx_utterances_conversation', 'conversation_id', 'sequence_number'),
        Index('idx_utterances_speaker', 'conversation_id', 'speaker_id'),
        Index('idx_utterances_chunk', 'chunk_id'),
        Index('idx_utterances_node', 'node_id'),
        Index('idx_utterances_thread', 'thread_id'),
        Index('idx_utterances_timestamp', 'conversation_id', 'timestamp_start'),
    )


class Node(Base):
    """Analyzed conversational topic/segment"""
    __tablename__ = "nodes"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    node_name = Column(Text, nullable=False)

    # Content
    summary = Column(Text, nullable=False)
    key_points = Column(ARRAY(Text))

    # Type & Hierarchy
    node_type = Column(Text, default='conversational_thread')
    level = Column(Integer, default=1)  # Hierarchy level for zoom
    parent_id = Column(UUID(as_uuid=True), ForeignKey('nodes.id'))
    children_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Flags
    is_bookmark = Column(Boolean, default=False)
    is_contextual_progress = Column(Boolean, default=False)
    is_tangent = Column(Boolean, default=False)
    is_crux = Column(Boolean, default=False)

    # Temporal Flow
    predecessor_id = Column(UUID(as_uuid=True), ForeignKey('nodes.id'))
    successor_id = Column(UUID(as_uuid=True), ForeignKey('nodes.id'))

    # Source Data
    chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    utterance_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Speakers
    speaker_info = Column(JSONB)  # Primary speaker, contribution %
    speaker_transitions = Column(ARRAY(JSONB))  # Speaker handoffs
    dialogue_type = Column(Text)  # 'monologue', 'dialogue', 'multi-party', 'consensus'

    # Claims
    claim_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Temporal
    timestamp_start = Column(Float)
    timestamp_end = Column(Float)
    duration_seconds = Column(Float)

    # Clustering & Display
    cluster_info = Column(JSONB)  # Auto-clustering metadata
    display_preferences = Column(JSONB)  # Visualization settings

    # Canvas Position (for Obsidian export)
    canvas_x = Column(Integer)
    canvas_y = Column(Integer)
    canvas_width = Column(Integer, default=350)
    canvas_height = Column(Integer, default=200)

    # Zoom visibility
    zoom_level_visible = Column(ARRAY(Integer))  # Which zoom levels show this node

    # Metadata
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "dialogue_type IS NULL OR dialogue_type IN ('monologue', 'dialogue', 'multi-party', 'consensus')",
            name='valid_dialogue_type'
        ),
        Index('idx_nodes_conversation', 'conversation_id'),
        Index('idx_nodes_temporal', 'conversation_id', 'timestamp_start'),
        Index('idx_nodes_speaker', 'conversation_id', text("((speaker_info->>'primary_speaker'))")),
        Index('idx_nodes_bookmarks', 'conversation_id', postgresql_where=text("is_bookmark = true")),
        Index('idx_nodes_tangents', 'conversation_id', postgresql_where=text("is_tangent = true")),
        Index('idx_nodes_level', 'conversation_id', 'level'),
    )


class Relationship(Base):
    """Edges/connections between nodes"""
    __tablename__ = "relationships"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)

    # Endpoints
    from_node_id = Column(UUID(as_uuid=True), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False)

    # Type
    relationship_type = Column(Text, nullable=False)
    relationship_subtype = Column(Text)

    # Description
    explanation = Column(Text)

    # Strength
    strength = Column(Float, default=1.0)
    confidence = Column(Float, default=1.0)

    # Evidence
    supporting_utterance_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Direction
    is_bidirectional = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("from_node_id != to_node_id", name='no_self_reference'),
        CheckConstraint("strength BETWEEN 0 AND 1", name='valid_strength'),
        CheckConstraint("confidence BETWEEN 0 AND 1", name='valid_confidence'),
        Index('idx_relationships_from', 'from_node_id'),
        Index('idx_relationships_to', 'to_node_id'),
        Index('idx_relationships_type', 'conversation_id', 'relationship_type'),
    )


class Cluster(Base):
    """Hierarchical node grouping"""
    __tablename__ = "clusters"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    cluster_name = Column(Text, nullable=False)

    # Hierarchy
    level = Column(Integer, nullable=False)  # 2=topics, 3=themes, etc.
    parent_cluster_id = Column(UUID(as_uuid=True), ForeignKey('clusters.id'))

    # Members
    node_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    child_cluster_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Summary
    summary = Column(Text)
    key_themes = Column(ARRAY(Text))

    # Metadata
    auto_generated = Column(Boolean, default=True)
    clustering_algorithm = Column(Text)  # 'semantic', 'temporal', 'speaker', 'manual'
    clustering_confidence = Column(Float)

    # Display
    color = Column(Text)
    icon = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_clusters_conversation', 'conversation_id'),
        Index('idx_clusters_level', 'conversation_id', 'level'),
    )


class EditsLog(Base):
    """Training data from user corrections"""
    __tablename__ = "edits_log"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)

    # Target
    target_type = Column(Text, nullable=False)  # 'node', 'relationship', 'cluster', 'speaker_attribution'
    target_id = Column(UUID(as_uuid=True), nullable=False)

    # Edit
    field_name = Column(Text, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)

    # Context
    edit_type = Column(Text, nullable=False)  # 'correction', 'addition', 'deletion', 'merge', 'split'
    user_comment = Column(Text)

    # User
    user_id = Column(Text, nullable=False)
    user_confidence = Column(Float, default=1.0)

    # Training
    exported_for_training = Column(Boolean, default=False)
    training_dataset_id = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "target_type IN ('node', 'relationship', 'cluster', 'speaker_attribution', 'claim', 'utterance')",
            name='valid_target_type'
        ),
        CheckConstraint(
            "edit_type IN ('correction', 'addition', 'deletion', 'merge', 'split')",
            name='valid_edit_type'
        ),
        Index('idx_edits_conversation', 'conversation_id'),
        Index('idx_edits_target', 'target_type', 'target_id'),
        Index('idx_edits_training', 'exported_for_training', postgresql_where=text("exported_for_training = false")),
    )


class APICallsLog(Base):
    """LLM API call tracking and cost monitoring"""
    __tablename__ = "api_calls_log"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='SET NULL'))
    endpoint = Column(Text, nullable=False)  # Which API endpoint triggered this
    feature = Column(Text, nullable=False)  # 'node_generation', 'claim_detection', 'bias_detection', etc.

    # API Details
    provider = Column(Text, nullable=False)  # 'openai', 'anthropic', 'google'
    model = Column(Text, nullable=False)  # 'gpt-4', 'claude-sonnet-4', etc.

    # Tokens
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # Cost (USD)
    prompt_cost = Column(Float, nullable=False)
    completion_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)

    # Performance
    latency_ms = Column(Integer)  # Response time in milliseconds
    status = Column(Text, nullable=False)  # 'success', 'error', 'timeout'
    error_message = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    # Metadata
    request_id = Column(Text)  # Provider's request ID for debugging

    __table_args__ = (
        Index('idx_api_calls_conversation', 'conversation_id'),
        Index('idx_api_calls_feature', 'feature'),
        Index('idx_api_calls_provider_model', 'provider', 'model'),
        Index('idx_api_calls_started', 'started_at'),
        Index('idx_api_calls_cost', 'total_cost'),
    )
