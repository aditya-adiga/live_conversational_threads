"""Add analysis tables for Weeks 11-13

Revision ID: add_analysis_weeks_11_13
Revises: 732e0cd9a870
Create Date: 2025-11-12

This migration creates the analysis tables for:
- Week 11: Simulacra Level Detection (simulacra_analysis)
- Week 12: Cognitive Bias Detection (bias_analysis)
- Week 13: Implicit Frame Detection (frame_analysis)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_analysis_weeks_11_13'
down_revision: Union[str, Sequence[str], None] = '732e0cd9a870'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Week 11: Simulacra Analysis table
    op.create_table(
        'simulacra_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text()),
        sa.Column('key_indicators', postgresql.JSONB()),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('level >= 1 AND level <= 4', name='check_simulacra_level'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_simulacra_confidence')
    )

    # Create indexes for simulacra_analysis
    op.create_index('idx_simulacra_node', 'simulacra_analysis', ['node_id'])
    op.create_index('idx_simulacra_conversation', 'simulacra_analysis', ['conversation_id'])
    op.create_index('idx_simulacra_level', 'simulacra_analysis', ['level'])

    # Week 12: Bias Analysis table
    op.create_table(
        'bias_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('bias_type', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('evidence', postgresql.JSONB()),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('severity >= 0.0 AND severity <= 1.0', name='check_bias_severity'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_bias_confidence')
    )

    # Create indexes for bias_analysis
    op.create_index('idx_bias_node', 'bias_analysis', ['node_id'])
    op.create_index('idx_bias_conversation', 'bias_analysis', ['conversation_id'])
    op.create_index('idx_bias_type', 'bias_analysis', ['bias_type'])
    op.create_index('idx_bias_category', 'bias_analysis', ['category'])

    # Week 13: Frame Analysis table
    op.create_table(
        'frame_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('frame_type', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('evidence', postgresql.JSONB()),
        sa.Column('assumptions', postgresql.JSONB()),
        sa.Column('implications', sa.Text()),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('strength >= 0.0 AND strength <= 1.0', name='check_frame_strength'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_frame_confidence')
    )

    # Create indexes for frame_analysis
    op.create_index('idx_frame_node', 'frame_analysis', ['node_id'])
    op.create_index('idx_frame_conversation', 'frame_analysis', ['conversation_id'])
    op.create_index('idx_frame_type', 'frame_analysis', ['frame_type'])
    op.create_index('idx_frame_category', 'frame_analysis', ['category'])


def downgrade() -> None:
    # Drop frame_analysis
    op.drop_index('idx_frame_category', table_name='frame_analysis')
    op.drop_index('idx_frame_type', table_name='frame_analysis')
    op.drop_index('idx_frame_conversation', table_name='frame_analysis')
    op.drop_index('idx_frame_node', table_name='frame_analysis')
    op.drop_table('frame_analysis')

    # Drop bias_analysis
    op.drop_index('idx_bias_category', table_name='bias_analysis')
    op.drop_index('idx_bias_type', table_name='bias_analysis')
    op.drop_index('idx_bias_conversation', table_name='bias_analysis')
    op.drop_index('idx_bias_node', table_name='bias_analysis')
    op.drop_table('bias_analysis')

    # Drop simulacra_analysis
    op.drop_index('idx_simulacra_level', table_name='simulacra_analysis')
    op.drop_index('idx_simulacra_conversation', table_name='simulacra_analysis')
    op.drop_index('idx_simulacra_node', table_name='simulacra_analysis')
    op.drop_table('simulacra_analysis')
