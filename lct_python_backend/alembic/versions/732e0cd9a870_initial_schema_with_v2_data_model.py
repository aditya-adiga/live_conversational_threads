"""Initial schema with V2 data model

Revision ID: 732e0cd9a870
Revises:
Create Date: 2025-11-11

This migration creates the complete V2 schema including:
- conversations (top-level container)
- utterances (atomic speech/text units)
- nodes (analyzed topics/segments)
- relationships (edges between nodes)
- clusters (hierarchical grouping)
- edits_log (training data from corrections)
- api_calls_log (cost tracking)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '732e0cd9a870'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_name', sa.Text(), nullable=False),
        sa.Column('conversation_type', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_metadata', postgresql.JSONB()),
        sa.Column('participant_count', sa.Integer(), server_default='0'),
        sa.Column('participants', postgresql.ARRAY(postgresql.JSONB())),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('goals', postgresql.ARRAY(postgresql.JSONB())),
        sa.Column('goal_progress', postgresql.JSONB()),
        sa.Column('gcs_path', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('owner_id', sa.Text(), nullable=False),
        sa.Column('visibility', sa.Text(), server_default='private'),
        sa.Column('shared_with', postgresql.ARRAY(sa.Text())),
        sa.Column('total_utterances', sa.Integer(), server_default='0'),
        sa.Column('total_words', sa.Integer(), server_default='0'),
        sa.Column('total_nodes', sa.Integer(), server_default='0'),
        sa.Column('total_claims', sa.Integer(), server_default='0'),
        sa.Column('tsv_search', postgresql.TSVECTOR()),
        sa.CheckConstraint("conversation_type IN ('live_audio', 'transcript', 'chat', 'hybrid')", name='valid_conversation_type'),
        sa.CheckConstraint("visibility IN ('private', 'shared', 'public')", name='valid_visibility')
    )

    # Create indexes for conversations
    op.create_index('idx_conversations_owner', 'conversations', ['owner_id'])
    op.create_index('idx_conversations_started', 'conversations', ['started_at'])
    op.create_index('idx_conversations_tsv', 'conversations', ['tsv_search'], postgresql_using='gin')

    # Create utterances table
    op.create_table(
        'utterances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('text_cleaned', sa.Text()),
        sa.Column('speaker_id', sa.Text(), nullable=False),
        sa.Column('speaker_name', sa.Text()),
        sa.Column('speaker_role', sa.Text()),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('timestamp_start', sa.Float()),
        sa.Column('timestamp_end', sa.Float()),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True)),
        sa.Column('node_id', postgresql.UUID(as_uuid=True)),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True)),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('language', sa.Text(), server_default='en'),
        sa.Column('emotion', sa.Text()),
        sa.Column('energy_level', sa.Float()),
        sa.Column('platform_metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "(timestamp_start IS NULL AND timestamp_end IS NULL) OR "
            "(timestamp_end IS NULL) OR "
            "(timestamp_end >= timestamp_start)",
            name='valid_timestamps'
        )
    )

    # Create indexes for utterances
    op.create_index('idx_utterances_conversation', 'utterances', ['conversation_id', 'sequence_number'])
    op.create_index('idx_utterances_speaker', 'utterances', ['conversation_id', 'speaker_id'])
    op.create_index('idx_utterances_chunk', 'utterances', ['chunk_id'])
    op.create_index('idx_utterances_node', 'utterances', ['node_id'])
    op.create_index('idx_utterances_thread', 'utterances', ['thread_id'])
    op.create_index('idx_utterances_timestamp', 'utterances', ['conversation_id', 'timestamp_start'])

    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_name', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_points', postgresql.ARRAY(sa.Text())),
        sa.Column('node_type', sa.Text(), server_default='conversational_thread'),
        sa.Column('level', sa.Integer(), server_default='1'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True)),
        sa.Column('children_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('is_bookmark', sa.Boolean(), server_default='false'),
        sa.Column('is_contextual_progress', sa.Boolean(), server_default='false'),
        sa.Column('is_tangent', sa.Boolean(), server_default='false'),
        sa.Column('is_crux', sa.Boolean(), server_default='false'),
        sa.Column('predecessor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('successor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('chunk_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('utterance_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('speaker_info', postgresql.JSONB()),
        sa.Column('speaker_transitions', postgresql.ARRAY(postgresql.JSONB())),
        sa.Column('dialogue_type', sa.Text()),
        sa.Column('claim_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('timestamp_start', sa.Float()),
        sa.Column('timestamp_end', sa.Float()),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('cluster_info', postgresql.JSONB()),
        sa.Column('display_preferences', postgresql.JSONB()),
        sa.Column('canvas_x', sa.Integer()),
        sa.Column('canvas_y', sa.Integer()),
        sa.Column('canvas_width', sa.Integer(), server_default='350'),
        sa.Column('canvas_height', sa.Integer(), server_default='200'),
        sa.Column('zoom_level_visible', postgresql.ARRAY(sa.Integer())),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['nodes.id']),
        sa.ForeignKeyConstraint(['predecessor_id'], ['nodes.id']),
        sa.ForeignKeyConstraint(['successor_id'], ['nodes.id']),
        sa.CheckConstraint(
            "dialogue_type IS NULL OR dialogue_type IN ('monologue', 'dialogue', 'multi-party', 'consensus')",
            name='valid_dialogue_type'
        )
    )

    # Create indexes for nodes
    op.create_index('idx_nodes_conversation', 'nodes', ['conversation_id'])
    op.create_index('idx_nodes_temporal', 'nodes', ['conversation_id', 'timestamp_start'])
    op.create_index('idx_nodes_level', 'nodes', ['conversation_id', 'level'])
    op.execute("CREATE INDEX idx_nodes_speaker ON nodes(conversation_id, ((speaker_info->>'primary_speaker')))")
    op.execute("CREATE INDEX idx_nodes_bookmarks ON nodes(conversation_id) WHERE is_bookmark = true")
    op.execute("CREATE INDEX idx_nodes_tangents ON nodes(conversation_id) WHERE is_tangent = true")

    # Create relationships table
    op.create_table(
        'relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.Text(), nullable=False),
        sa.Column('relationship_subtype', sa.Text()),
        sa.Column('explanation', sa.Text()),
        sa.Column('strength', sa.Float(), server_default='1.0'),
        sa.Column('confidence', sa.Float(), server_default='1.0'),
        sa.Column('supporting_utterance_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('is_bidirectional', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.CheckConstraint('from_node_id != to_node_id', name='no_self_reference'),
        sa.CheckConstraint('strength BETWEEN 0 AND 1', name='valid_strength'),
        sa.CheckConstraint('confidence BETWEEN 0 AND 1', name='valid_confidence')
    )

    # Create indexes for relationships
    op.create_index('idx_relationships_from', 'relationships', ['from_node_id'])
    op.create_index('idx_relationships_to', 'relationships', ['to_node_id'])
    op.create_index('idx_relationships_type', 'relationships', ['conversation_id', 'relationship_type'])

    # Create clusters table
    op.create_table(
        'clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_name', sa.Text(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('parent_cluster_id', postgresql.UUID(as_uuid=True)),
        sa.Column('node_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('child_cluster_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('summary', sa.Text()),
        sa.Column('key_themes', postgresql.ARRAY(sa.Text())),
        sa.Column('auto_generated', sa.Boolean(), server_default='true'),
        sa.Column('clustering_algorithm', sa.Text()),
        sa.Column('clustering_confidence', sa.Float()),
        sa.Column('color', sa.Text()),
        sa.Column('icon', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_cluster_id'], ['clusters.id'])
    )

    # Create indexes for clusters
    op.create_index('idx_clusters_conversation', 'clusters', ['conversation_id'])
    op.create_index('idx_clusters_level', 'clusters', ['conversation_id', 'level'])

    # Create edits_log table
    op.create_table(
        'edits_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.Text(), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.Text(), nullable=False),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('edit_type', sa.Text(), nullable=False),
        sa.Column('user_comment', sa.Text()),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('user_confidence', sa.Float(), server_default='1.0'),
        sa.Column('exported_for_training', sa.Boolean(), server_default='false'),
        sa.Column('training_dataset_id', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "target_type IN ('node', 'relationship', 'cluster', 'speaker_attribution', 'claim', 'utterance')",
            name='valid_target_type'
        ),
        sa.CheckConstraint(
            "edit_type IN ('correction', 'addition', 'deletion', 'merge', 'split')",
            name='valid_edit_type'
        )
    )

    # Create indexes for edits_log
    op.create_index('idx_edits_conversation', 'edits_log', ['conversation_id'])
    op.create_index('idx_edits_target', 'edits_log', ['target_type', 'target_id'])
    op.execute("CREATE INDEX idx_edits_training ON edits_log(exported_for_training) WHERE exported_for_training = false")

    # Create api_calls_log table
    op.create_table(
        'api_calls_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('feature', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('prompt_cost', sa.Float(), nullable=False),
        sa.Column('completion_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Integer()),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('request_id', sa.Text()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL')
    )

    # Create indexes for api_calls_log
    op.create_index('idx_api_calls_conversation', 'api_calls_log', ['conversation_id'])
    op.create_index('idx_api_calls_feature', 'api_calls_log', ['feature'])
    op.create_index('idx_api_calls_provider_model', 'api_calls_log', ['provider', 'model'])
    op.create_index('idx_api_calls_started', 'api_calls_log', ['started_at'])
    op.create_index('idx_api_calls_cost', 'api_calls_log', ['total_cost'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('api_calls_log')
    op.drop_table('edits_log')
    op.drop_table('clusters')
    op.drop_table('relationships')
    op.drop_table('nodes')
    op.drop_table('utterances')
    op.drop_table('conversations')

    # Drop UUID extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
