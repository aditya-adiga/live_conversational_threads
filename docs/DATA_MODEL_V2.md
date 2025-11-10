# Live Conversational Threads - Data Model V2

**Version**: 2.0
**Date**: 2025-11-10
**Status**: Proposed

## Overview

This document defines a comprehensive data model that supports:
- Multi-speaker conversations with attribution
- Claim taxonomy (factual, normative, worldview)
- Parallel thread tracking
- Goal tracking and drift detection
- Bandwidth metrics and speaker analytics
- Multi-source aggregation (Meet, Slack, Discord, etc.)
- Rich relationship modeling
- Temporal and causal analysis

## Design Principles

1. **Separation of Concerns**: Raw data (utterances) separate from analyzed data (nodes, claims)
2. **Immutability**: Original data never modified, only augmented
3. **Flexibility**: Support multiple conversation types (live, transcript, chat, etc.)
4. **Queryability**: Enable complex queries across speakers, topics, time, relationships
5. **Extensibility**: Easy to add new metadata without schema changes (JSONB)
6. **Privacy-First**: Clear data ownership, easy deletion/export

---

## Core Entities

### 1. Conversation (Top-level container)

```sql
CREATE TABLE conversations (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_name TEXT NOT NULL,
    conversation_type TEXT NOT NULL, -- 'live_audio', 'transcript', 'chat', 'hybrid'

    -- Source
    source_type TEXT NOT NULL, -- 'audio_stream', 'google_meet', 'slack', 'discord', etc.
    source_metadata JSONB, -- Platform-specific data (meeting_id, channel_id, etc.)

    -- Participants
    participant_count INTEGER DEFAULT 0,
    participants JSONB[], -- Array of {id, name, role, email?, avatar_url?}

    -- Temporal
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- Goals & Intent
    goals JSONB[], -- Array of {goal_type, description, target_metric}
    goal_progress JSONB, -- Current progress towards goals

    -- Storage
    gcs_path TEXT, -- Path to full conversation JSON in GCS

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ, -- Soft delete

    -- Privacy
    owner_id TEXT NOT NULL, -- User who owns this data
    visibility TEXT DEFAULT 'private', -- 'private', 'shared', 'public'
    shared_with TEXT[], -- User IDs with access

    -- Analytics (cached)
    total_utterances INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    total_nodes INTEGER DEFAULT 0,
    total_claims INTEGER DEFAULT 0,

    -- Indexing
    tsv_search TSVECTOR, -- Full-text search vector

    CONSTRAINT valid_type CHECK (conversation_type IN ('live_audio', 'transcript', 'chat', 'hybrid')),
    CONSTRAINT valid_visibility CHECK (visibility IN ('private', 'shared', 'public'))
);

CREATE INDEX idx_conversations_owner ON conversations(owner_id);
CREATE INDEX idx_conversations_started ON conversations(started_at DESC);
CREATE INDEX idx_conversations_tsv ON conversations USING GIN(tsv_search);
```

**Goal Schema:**
```json
{
  "goal_type": "learn" | "decide" | "build_rapport" | "brainstorm" | "resolve_conflict" | "custom",
  "description": "Understand the new API design",
  "target_metric": "coverage_percentage",
  "target_value": 80,
  "weight": 1.0
}
```

---

### 2. Utterance (Atomic unit of speech/text)

```sql
CREATE TABLE utterances (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Content
    text TEXT NOT NULL,
    text_cleaned TEXT, -- Normalized, disfluencies removed

    -- Speaker
    speaker_id TEXT NOT NULL, -- 'Speaker 1', user_id, etc.
    speaker_name TEXT, -- Human-readable name
    speaker_role TEXT, -- 'facilitator', 'participant', 'observer'

    -- Temporal
    sequence_number INTEGER NOT NULL, -- Order in conversation
    timestamp_start FLOAT, -- Seconds from conversation start
    timestamp_end FLOAT,
    duration_seconds FLOAT,

    -- Context
    chunk_id UUID, -- Which chunk this belongs to
    node_id UUID, -- Which analyzed node this contributes to
    thread_id UUID, -- Which parallel thread (if any)

    -- Metadata
    confidence_score FLOAT, -- Transcription confidence (0-1)
    language TEXT DEFAULT 'en',
    emotion TEXT, -- 'neutral', 'excited', 'frustrated', etc. (optional)
    energy_level FLOAT, -- Speaking energy/intensity (0-1, optional)

    -- Source-specific
    platform_metadata JSONB, -- Platform-specific data (message_id, reactions, etc.)

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_sequence UNIQUE(conversation_id, sequence_number),
    CONSTRAINT valid_timestamps CHECK (
        (timestamp_start IS NULL AND timestamp_end IS NULL) OR
        (timestamp_end IS NULL) OR
        (timestamp_end >= timestamp_start)
    )
);

CREATE INDEX idx_utterances_conversation ON utterances(conversation_id, sequence_number);
CREATE INDEX idx_utterances_speaker ON utterances(conversation_id, speaker_id);
CREATE INDEX idx_utterances_chunk ON utterances(chunk_id);
CREATE INDEX idx_utterances_node ON utterances(node_id);
CREATE INDEX idx_utterances_thread ON utterances(thread_id);
CREATE INDEX idx_utterances_timestamp ON utterances(conversation_id, timestamp_start);
```

---

### 3. Chunk (Processing unit for LLM)

```sql
CREATE TABLE chunks (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Content
    text TEXT NOT NULL, -- Aggregated utterance text
    word_count INTEGER,

    -- Temporal
    sequence_number INTEGER NOT NULL,
    timestamp_start FLOAT,
    timestamp_end FLOAT,

    -- Utterances
    utterance_ids UUID[] NOT NULL, -- References utterances
    utterance_count INTEGER,

    -- Speakers
    speaker_ids TEXT[] NOT NULL,
    speaker_distribution JSONB, -- {speaker_id: word_count}
    dominant_speaker TEXT, -- Speaker with most content

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_chunk_sequence UNIQUE(conversation_id, sequence_number)
);

CREATE INDEX idx_chunks_conversation ON chunks(conversation_id, sequence_number);
CREATE INDEX idx_chunks_processed ON chunks(conversation_id, processed);
```

---

### 4. Node (Analyzed conversational topic)

```sql
CREATE TABLE nodes (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    node_name TEXT NOT NULL, -- Human-readable topic name

    -- Content
    summary TEXT NOT NULL,
    key_points TEXT[],

    -- Type
    node_type TEXT DEFAULT 'conversational_thread',
    is_bookmark BOOLEAN DEFAULT FALSE,
    is_contextual_progress BOOLEAN DEFAULT FALSE,
    is_tangent BOOLEAN DEFAULT FALSE, -- Unresolved divergence
    is_crux BOOLEAN DEFAULT FALSE, -- Key disagreement point

    -- Temporal Flow
    predecessor_id UUID REFERENCES nodes(id),
    successor_id UUID REFERENCES nodes(id),

    -- Source Data
    chunk_ids UUID[] NOT NULL, -- Which chunks contributed
    utterance_ids UUID[], -- Direct utterance references

    -- Speakers
    speaker_info JSONB, -- Primary speaker, contribution %
    speaker_transitions JSONB[], -- Speaker handoffs within node
    dialogue_type TEXT, -- 'monologue', 'dialogue', 'multi-party', 'consensus'

    -- Claims
    claim_ids UUID[], -- References to claims table

    -- Temporal
    timestamp_start FLOAT,
    timestamp_end FLOAT,
    duration_seconds FLOAT,

    -- Position (for visualization)
    canvas_x INTEGER,
    canvas_y INTEGER,
    canvas_width INTEGER DEFAULT 350,
    canvas_height INTEGER DEFAULT 200,

    -- Metadata
    confidence_score FLOAT, -- LLM confidence in this segmentation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_node_name UNIQUE(conversation_id, node_name),
    CONSTRAINT valid_dialogue_type CHECK (
        dialogue_type IS NULL OR
        dialogue_type IN ('monologue', 'dialogue', 'multi-party', 'consensus')
    )
);

CREATE INDEX idx_nodes_conversation ON nodes(conversation_id);
CREATE INDEX idx_nodes_temporal ON nodes(conversation_id, timestamp_start);
CREATE INDEX idx_nodes_speaker ON nodes(conversation_id, ((speaker_info->>'primary_speaker')));
CREATE INDEX idx_nodes_bookmarks ON nodes(conversation_id) WHERE is_bookmark = TRUE;
CREATE INDEX idx_nodes_tangents ON nodes(conversation_id) WHERE is_tangent = TRUE;
```

**Speaker Info Schema:**
```json
{
  "primary_speaker": "speaker_1",
  "speaker_name": "Alice Chen",
  "contribution_percentage": 75.5,
  "secondary_speakers": [
    {"speaker_id": "speaker_2", "percentage": 24.5}
  ]
}
```

**Speaker Transition Schema:**
```json
{
  "from_speaker": "speaker_1",
  "to_speaker": "speaker_2",
  "utterance_index": 5,
  "transition_type": "question_answer" | "interruption" | "handoff" | "agreement",
  "context_snippet": "So what do you think about...?"
}
```

---

### 5. Relationship (Contextual connections between nodes)

```sql
CREATE TABLE relationships (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Endpoints
    from_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,

    -- Type
    relationship_type TEXT NOT NULL,
    relationship_subtype TEXT,

    -- Description
    explanation TEXT, -- Human-readable explanation

    -- Strength
    strength FLOAT DEFAULT 1.0, -- 0-1, how strong is this connection
    confidence FLOAT DEFAULT 1.0, -- 0-1, LLM confidence

    -- Evidence
    supporting_utterance_ids UUID[],

    -- Direction
    is_bidirectional BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_relationship UNIQUE(from_node_id, to_node_id, relationship_type),
    CONSTRAINT no_self_reference CHECK (from_node_id != to_node_id),
    CONSTRAINT valid_strength CHECK (strength BETWEEN 0 AND 1),
    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0 AND 1)
);

CREATE INDEX idx_relationships_from ON relationships(from_node_id);
CREATE INDEX idx_relationships_to ON relationships(to_node_id);
CREATE INDEX idx_relationships_type ON relationships(conversation_id, relationship_type);

-- Relationship types:
-- 'temporal_next' - Sequential flow
-- 'contextual_related' - Topically related
-- 'elaborates' - Node B elaborates on node A
-- 'contradicts' - Node B contradicts node A
-- 'supports' - Node B supports argument in node A
-- 'questions' - Node B questions node A
-- 'answers' - Node B answers question in node A
-- 'builds_on' - Node B builds on idea from node A
-- 'diverges' - Node B diverges from node A (tangent)
-- 'resolves' - Node B resolves issue in node A
-- 'revisits' - Node B returns to topic from node A
-- 'depends_on' - Node B assumes/requires node A
-- 'crux' - Fundamental disagreement point
```

---

### 6. Claim (Factual, normative, or worldview assertion)

```sql
CREATE TABLE claims (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    node_id UUID REFERENCES nodes(id) ON DELETE SET NULL,

    -- Content
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL, -- 'factual', 'normative', 'worldview'

    -- Speaker
    speaker_id TEXT NOT NULL,
    speaker_name TEXT,

    -- Source
    utterance_ids UUID[] NOT NULL,
    source_quote TEXT, -- Exact quote from transcript

    -- Classification
    domain TEXT, -- 'science', 'politics', 'ethics', 'business', etc.
    ideology TEXT, -- 'dataism', 'humanism', 'accelerationism', etc. (for worldview)

    -- Verification (for factual claims)
    is_verified BOOLEAN,
    verification_status TEXT, -- 'true', 'false', 'partially_true', 'unverified', 'pending'
    verification_explanation TEXT,
    verification_citations JSONB[], -- [{title, url, date}]
    verified_at TIMESTAMPTZ,

    -- Confidence
    extraction_confidence FLOAT, -- How confident we are this is a claim
    classification_confidence FLOAT, -- How confident in the type

    -- Relationships to other claims
    supports_claim_ids UUID[], -- Claims this supports
    contradicts_claim_ids UUID[], -- Claims this contradicts
    assumes_claim_ids UUID[], -- Prerequisites (especially for worldview → normative)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_claim_type CHECK (claim_type IN ('factual', 'normative', 'worldview')),
    CONSTRAINT valid_verification CHECK (
        claim_type != 'factual' OR verification_status IN
        ('true', 'false', 'partially_true', 'unverified', 'pending')
    )
);

CREATE INDEX idx_claims_conversation ON claims(conversation_id);
CREATE INDEX idx_claims_node ON claims(node_id);
CREATE INDEX idx_claims_type ON claims(conversation_id, claim_type);
CREATE INDEX idx_claims_speaker ON claims(conversation_id, speaker_id);
CREATE INDEX idx_claims_verification ON claims(conversation_id, verification_status)
    WHERE claim_type = 'factual';
```

**Claim Type Examples:**
```sql
-- Factual: Verifiable against external data
INSERT INTO claims (claim_text, claim_type) VALUES
    ('The API latency is 200ms', 'factual'),
    ('We had 1000 users last month', 'factual');

-- Normative: Value judgments, "should" statements
INSERT INTO claims (claim_text, claim_type) VALUES
    ('We should prioritize user experience over features', 'normative'),
    ('Fast iteration is more important than perfection', 'normative');

-- Worldview: Ideological assumptions, axioms
INSERT INTO claims (claim_text, claim_type, ideology) VALUES
    ('Data-driven decisions are always superior to intuition', 'worldview', 'dataism'),
    ('Individual liberty should be maximized', 'worldview', 'libertarianism'),
    ('Accelerating AI progress is humanity''s highest priority', 'worldview', 'accelerationism');
```

---

### 7. Thread (Parallel conversation strand)

```sql
CREATE TABLE threads (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    thread_name TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'active', -- 'active', 'paused', 'resolved', 'abandoned'

    -- Content
    summary TEXT,
    initiating_node_id UUID REFERENCES nodes(id),

    -- Participants
    speaker_ids TEXT[],

    -- Temporal
    started_at FLOAT, -- Seconds from conversation start
    paused_at FLOAT,
    resumed_at FLOAT,
    resolved_at FLOAT,

    -- Pause/Resume
    pause_reason TEXT, -- 'interrupted', 'natural_lull', 'priority_shift', etc.
    pause_context TEXT, -- What was being discussed when paused
    resume_prompt TEXT, -- Suggested prompt to resume ("Earlier you were discussing...")

    -- Retrieval
    retrieval_relevance FLOAT, -- Current relevance score (0-1)
    retrieval_context JSONB, -- Keywords, concepts for retrieval
    retrieval_priority INTEGER DEFAULT 0, -- User-set priority

    -- Nodes in this thread
    node_ids UUID[],

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'resolved', 'abandoned'))
);

CREATE INDEX idx_threads_conversation ON threads(conversation_id);
CREATE INDEX idx_threads_status ON threads(conversation_id, status);
CREATE INDEX idx_threads_paused ON threads(conversation_id, paused_at)
    WHERE status = 'paused';
CREATE INDEX idx_threads_relevance ON threads(conversation_id, retrieval_relevance DESC)
    WHERE status = 'paused';
```

---

### 8. Speaker (Participant profile)

```sql
CREATE TABLE speakers (
    -- Identity
    id TEXT PRIMARY KEY, -- 'speaker_1', user_id, email, etc.
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Profile
    display_name TEXT,
    email TEXT,
    avatar_url TEXT,
    role TEXT, -- 'facilitator', 'participant', 'observer', 'expert', etc.

    -- Analytics (cached)
    total_utterances INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    speaking_time_seconds FLOAT DEFAULT 0,

    -- Participation
    participation_percentage FLOAT, -- Of total conversation
    interruption_count INTEGER DEFAULT 0,
    interrupted_count INTEGER DEFAULT 0, -- Times interrupted by others

    -- Contributions
    topics_led TEXT[], -- Node names where they were primary speaker
    claims_made INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,

    -- Interaction
    most_interacted_with TEXT[], -- Other speaker IDs
    interaction_counts JSONB, -- {speaker_id: interaction_count}

    -- Energy/Sentiment (optional)
    avg_energy FLOAT, -- Average speaking energy
    sentiment_distribution JSONB, -- {positive: 0.6, neutral: 0.3, negative: 0.1}

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_speaker_conv UNIQUE(conversation_id, id)
);

CREATE INDEX idx_speakers_conversation ON speakers(conversation_id);
CREATE INDEX idx_speakers_participation ON speakers(conversation_id, participation_percentage DESC);
```

---

### 9. Goal Tracking

```sql
CREATE TABLE conversation_goals (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Goal Definition
    goal_type TEXT NOT NULL,
    description TEXT NOT NULL,
    target_metric TEXT, -- What to measure
    target_value FLOAT, -- Target threshold
    weight FLOAT DEFAULT 1.0, -- Importance weight

    -- Progress
    current_value FLOAT,
    progress_percentage FLOAT,
    is_achieved BOOLEAN DEFAULT FALSE,

    -- Tracking
    relevant_node_ids UUID[],
    drift_incidents INTEGER DEFAULT 0, -- Times conversation drifted away

    -- Timeline
    set_at TIMESTAMPTZ DEFAULT NOW(),
    achieved_at TIMESTAMPTZ,

    CONSTRAINT valid_goal_type CHECK (
        goal_type IN ('learn', 'decide', 'build_rapport', 'brainstorm',
                      'resolve_conflict', 'align', 'custom')
    )
);

CREATE INDEX idx_goals_conversation ON conversation_goals(conversation_id);
CREATE INDEX idx_goals_achieved ON conversation_goals(conversation_id, is_achieved);
```

---

### 10. Drift Events

```sql
CREATE TABLE drift_events (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Timing
    detected_at FLOAT, -- Seconds from conversation start
    duration_seconds FLOAT, -- How long the drift lasted

    -- Goal
    goal_id UUID REFERENCES conversation_goals(id),

    -- Drift Details
    original_topic TEXT, -- What was on-track
    drifted_topic TEXT, -- What it drifted to
    drift_severity FLOAT, -- 0-1, how far off track

    -- Nodes involved
    drift_node_ids UUID[],

    -- Resolution
    was_intentional BOOLEAN, -- User indicated intentional tangent
    was_productive BOOLEAN, -- Resulted in value despite drift
    returned_to_track BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drift_conversation ON drift_events(conversation_id, detected_at);
CREATE INDEX idx_drift_goal ON drift_events(goal_id);
```

---

### 11. Crux (Key disagreement points)

```sql
CREATE TABLE cruxes (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Definition
    crux_statement TEXT NOT NULL, -- The point of disagreement
    crux_type TEXT, -- 'factual', 'values', 'priorities', 'predictions', 'definitions'

    -- Participants
    speaker_positions JSONB NOT NULL, -- {speaker_id: {position, reasoning}}

    -- Related Content
    node_ids UUID[],
    claim_ids UUID[],

    -- Dependencies
    depends_on_crux_ids UUID[], -- Other cruxes this depends on

    -- Resolution
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_type TEXT, -- 'consensus', 'agree_to_disagree', 'tabled', 'one_convinced'
    resolution_summary TEXT,
    resolved_at FLOAT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cruxes_conversation ON cruxes(conversation_id);
CREATE INDEX idx_cruxes_unresolved ON cruxes(conversation_id) WHERE is_resolved = FALSE;
```

**Speaker Position Schema:**
```json
{
  "speaker_1": {
    "position": "Should use GraphQL",
    "reasoning": "More flexible, better for mobile clients",
    "confidence": 0.8,
    "claim_ids": ["uuid1", "uuid2"]
  },
  "speaker_2": {
    "position": "Should stick with REST",
    "reasoning": "Team expertise, simpler debugging",
    "confidence": 0.7,
    "claim_ids": ["uuid3"]
  }
}
```

---

### 12. Annotations (User corrections/feedback)

```sql
CREATE TABLE annotations (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Target
    target_type TEXT NOT NULL, -- 'node', 'claim', 'relationship', 'utterance'
    target_id UUID NOT NULL,

    -- Annotation
    annotation_type TEXT NOT NULL, -- 'correction', 'addition', 'flag', 'rating'
    annotation_text TEXT,

    -- User
    user_id TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_target_type CHECK (
        target_type IN ('node', 'claim', 'relationship', 'utterance', 'thread')
    ),
    CONSTRAINT valid_annotation_type CHECK (
        annotation_type IN ('correction', 'addition', 'flag', 'rating', 'note')
    )
);

CREATE INDEX idx_annotations_target ON annotations(target_type, target_id);
CREATE INDEX idx_annotations_conversation ON annotations(conversation_id);
```

---

## Views for Common Queries

### Speaker Interaction Network

```sql
CREATE MATERIALIZED VIEW speaker_interactions AS
SELECT
    u1.conversation_id,
    u1.speaker_id AS speaker_1,
    u2.speaker_id AS speaker_2,
    COUNT(*) AS interaction_count,
    ARRAY_AGG(DISTINCT n.node_name) AS shared_topics
FROM utterances u1
JOIN utterances u2 ON
    u1.conversation_id = u2.conversation_id AND
    u1.speaker_id != u2.speaker_id AND
    ABS(u1.sequence_number - u2.sequence_number) <= 3 -- Within 3 turns
LEFT JOIN nodes n ON u1.node_id = n.id
GROUP BY u1.conversation_id, u1.speaker_id, u2.speaker_id;

CREATE INDEX idx_speaker_interactions_conv ON speaker_interactions(conversation_id);
```

### Claim Dependency Graph

```sql
CREATE MATERIALIZED VIEW claim_dependencies AS
WITH RECURSIVE claim_tree AS (
    -- Base case: worldview claims (no dependencies)
    SELECT
        id,
        claim_text,
        claim_type,
        assumes_claim_ids,
        0 AS depth,
        ARRAY[id] AS path
    FROM claims
    WHERE claim_type = 'worldview' AND
          (assumes_claim_ids IS NULL OR array_length(assumes_claim_ids, 1) = 0)

    UNION ALL

    -- Recursive case: claims that depend on previous
    SELECT
        c.id,
        c.claim_text,
        c.claim_type,
        c.assumes_claim_ids,
        ct.depth + 1,
        ct.path || c.id
    FROM claims c
    JOIN claim_tree ct ON c.assumes_claim_ids @> ARRAY[ct.id]
    WHERE NOT c.id = ANY(ct.path) -- Prevent cycles
)
SELECT * FROM claim_tree;
```

### Active Thread Suggestions

```sql
CREATE VIEW paused_threads_for_retrieval AS
SELECT
    t.*,
    -- Relevance based on current conversation context
    -- (would be computed in application with current embedding similarity)
    COUNT(DISTINCT u.speaker_id) AS active_speakers_in_thread,
    MAX(u.timestamp_start) AS last_mentioned
FROM threads t
LEFT JOIN utterances u ON u.thread_id = t.id
WHERE t.status = 'paused'
GROUP BY t.id
ORDER BY
    t.retrieval_priority DESC,
    t.retrieval_relevance DESC,
    last_mentioned DESC;
```

---

## JSON Schemas for JSONB Fields

### Participant Schema
```json
{
  "id": "user_123 | speaker_1",
  "name": "Alice Chen",
  "role": "facilitator | participant | observer",
  "email": "alice@example.com",
  "avatar_url": "https://...",
  "platform_id": "slack:U123 | discord:456",
  "metadata": {
    "timezone": "America/Los_Angeles",
    "title": "Senior Engineer"
  }
}
```

### Platform Metadata (utterance level)
```json
{
  // Slack
  "platform": "slack",
  "message_id": "1234567890.123456",
  "channel_id": "C123456",
  "thread_ts": "1234567890.123456",
  "reactions": [{"emoji": "👍", "count": 3}],
  "attachments": ["url1", "url2"],

  // Discord
  "platform": "discord",
  "message_id": "987654321",
  "channel_id": "123456",
  "guild_id": "789",
  "mentions": ["user_id_1"],

  // Google Meet
  "platform": "google_meet",
  "meeting_id": "abc-defg-hij",
  "recording_url": "https://...",
  "is_host": false
}
```

### Verification Citation Schema
```json
{
  "title": "API Performance Report Q4 2024",
  "url": "https://docs.example.com/...",
  "source_type": "internal_doc | external_article | research_paper",
  "date": "2024-10-15",
  "relevance_score": 0.95,
  "excerpt": "The 95th percentile latency was measured at 185ms..."
}
```

---

## Data Flow Example

### Live Audio Conversation
```
1. Audio Stream → AssemblyAI
2. Create Conversation record (type: 'live_audio')
3. Real-time transcription → Utterance records (sequential)
4. Batch utterances → Chunk records (every 10k words)
5. Process Chunk → LLM generates Nodes, Claims, Relationships
6. Update Speaker analytics
7. Track Goals and detect Drift
8. Detect paused Threads
9. Calculate Cruxes if disagreement detected
```

### Transcript Import (Google Meet)
```
1. Upload .txt or Google Doc URL
2. Create Conversation record (type: 'transcript', source: 'google_meet')
3. Parse transcript → Utterance records with speaker attribution
4. Group utterances → Chunk records (speaker-aware boundaries)
5. Process Chunks → Nodes, Claims, Relationships
6. Calculate Speaker analytics
7. Detect Threads and Cruxes
8. Import complete → redirect to visualization
```

---

## Migration Strategy from V1

```sql
-- Step 1: Create new tables
-- (All CREATE TABLE statements above)

-- Step 2: Migrate existing conversations
INSERT INTO conversations (
    id, conversation_name, conversation_type, source_type,
    started_at, gcs_path, created_at, owner_id,
    total_nodes, total_claims
)
SELECT
    id,
    file_name,
    'live_audio', -- Assume all existing are live audio
    'audio_stream',
    created_at,
    gcs_path,
    created_at,
    'default_user', -- Assign default owner
    no_of_nodes,
    0 -- No claims in V1
FROM old_conversations;

-- Step 3: Migrate nodes (from GCS JSON files)
-- This requires application-level migration:
-- 1. Load each conversation JSON from GCS
-- 2. Parse graph_data array
-- 3. Insert into new nodes table
-- 4. Extract relationships and insert

-- Step 4: Backfill chunks from chunk_dict
-- Similar application-level migration

-- Step 5: Mark V1 data with metadata
UPDATE conversations SET source_metadata = '{"migrated_from_v1": true}'
WHERE source_type = 'audio_stream';
```

---

## Query Examples

### 1. Speaker Bandwidth Analysis
```sql
SELECT
    s.display_name,
    s.total_utterances,
    s.total_words,
    s.participation_percentage,
    ROUND(s.speaking_time_seconds / 60.0, 2) AS minutes_spoken,
    s.interruption_count
FROM speakers s
WHERE s.conversation_id = ?
ORDER BY s.participation_percentage DESC;
```

### 2. Claim Dependency Chain (Worldview → Normative → Factual)
```sql
WITH RECURSIVE chain AS (
    SELECT
        c.id, c.claim_text, c.claim_type, c.assumes_claim_ids,
        0 AS level, c.claim_text::TEXT AS chain_path
    FROM claims c
    WHERE c.id = ? -- Start from a specific claim

    UNION ALL

    SELECT
        parent.id, parent.claim_text, parent.claim_type, parent.assumes_claim_ids,
        chain.level + 1,
        chain.chain_path || ' → ' || parent.claim_text
    FROM claims parent
    JOIN chain ON parent.id = ANY(chain.assumes_claim_ids)
)
SELECT level, claim_type, claim_text, chain_path
FROM chain
ORDER BY level DESC;
```

### 3. Find Paused Threads Relevant to Current Topic
```sql
SELECT
    t.thread_name,
    t.summary,
    t.pause_context,
    t.resume_prompt,
    t.paused_at,
    similarity(t.retrieval_context->>'keywords', ?) AS relevance
FROM threads t
WHERE
    t.conversation_id = ? AND
    t.status = 'paused' AND
    similarity(t.retrieval_context->>'keywords', ?) > 0.3
ORDER BY relevance DESC, t.retrieval_priority DESC
LIMIT 5;
```

### 4. Detect Emerging Cruxes
```sql
-- Find opposing claims between speakers on same topic
SELECT
    c1.speaker_id AS speaker_1,
    c2.speaker_id AS speaker_2,
    c1.claim_text AS position_1,
    c2.claim_text AS position_2,
    n.node_name AS topic
FROM claims c1
JOIN claims c2 ON
    c1.node_id = c2.node_id AND
    c1.speaker_id != c2.speaker_id AND
    c1.id = ANY(c2.contradicts_claim_ids)
JOIN nodes n ON c1.node_id = n.id
WHERE c1.conversation_id = ?;
```

### 5. Goal Progress Tracking
```sql
SELECT
    g.description AS goal,
    g.target_value,
    g.current_value,
    ROUND(100.0 * g.current_value / g.target_value, 1) AS progress_pct,
    COUNT(n.id) AS relevant_nodes,
    g.drift_incidents
FROM conversation_goals g
LEFT JOIN nodes n ON n.id = ANY(g.relevant_node_ids)
WHERE g.conversation_id = ?
GROUP BY g.id;
```

---

## Performance Considerations

### Indexes
- All foreign keys indexed
- Timestamps indexed for temporal queries
- JSONB fields with common access patterns use GIN indexes
- Materialized views for expensive aggregations

### Partitioning
```sql
-- Partition large tables by conversation_id range or time
CREATE TABLE utterances_partitioned (LIKE utterances INCLUDING ALL)
PARTITION BY HASH (conversation_id);

-- Create 10 partitions
CREATE TABLE utterances_p0 PARTITION OF utterances_partitioned
    FOR VALUES WITH (MODULUS 10, REMAINDER 0);
-- ... repeat for p1-p9
```

### Caching Strategy
- Conversation-level aggregates cached in `conversations` table
- Speaker analytics cached in `speakers` table
- Materialized views refreshed on conversation completion
- Application-level caching for hot paths (Redis)

---

## Privacy & Compliance

### Data Deletion
```sql
-- Soft delete (default)
UPDATE conversations SET deleted_at = NOW() WHERE id = ?;

-- Hard delete (GDPR right to be forgotten)
DELETE FROM conversations WHERE id = ?; -- Cascades to all related tables

-- Export before delete
SELECT json_build_object(
    'conversation', row_to_json(c.*),
    'utterances', (SELECT json_agg(u.*) FROM utterances u WHERE u.conversation_id = c.id),
    'nodes', (SELECT json_agg(n.*) FROM nodes n WHERE n.conversation_id = c.id)
    -- ... etc
) FROM conversations c WHERE c.id = ?;
```

### Anonymization
```sql
-- Anonymize speaker names
UPDATE speakers SET
    display_name = 'Speaker ' || (ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at)),
    email = NULL,
    avatar_url = NULL
WHERE conversation_id = ?;

-- Anonymize claims
UPDATE claims SET speaker_name = NULL WHERE conversation_id = ?;
```

---

## Next Steps

1. **Review & Approve**: Team review of data model
2. **Prototype**: Implement core tables and test with sample data
3. **Migration Plan**: Detail V1 → V2 migration steps
4. **API Design**: Design REST/GraphQL API around this model
5. **Performance Testing**: Load test with realistic data volumes
6. **Privacy Audit**: Legal review of privacy features

---

## Open Questions

1. **Embeddings**: Should we store vector embeddings in Postgres (pgvector) or separate system (Pinecone)?
2. **Real-time**: How to efficiently stream updates to multiple connected clients?
3. **Archival**: What's the data retention policy? Move old conversations to cold storage?
4. **Scale**: What's the expected conversation size? (1k utterances? 10k? 100k?)
5. **Versioning**: Should nodes/claims be versioned (immutable log) or mutable?
6. **Multi-language**: How to handle non-English conversations?
