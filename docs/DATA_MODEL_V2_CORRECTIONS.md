# Data Model V2 - Corrections & Online Learning System

**Version**: 2.0 Addendum
**Date**: 2025-11-10
**Parent**: DATA_MODEL_V2.md

## Overview

Transcripts from Google Meet (or any ASR system) are **not ground truth**. This document extends the V2 data model to support:

1. **Audio Storage**: Original audio segments for re-transcription
2. **User Corrections**: Human feedback on transcription errors
3. **Context-Aware Corrections**: AI-inferred fixes using conversation context
4. **Online Learning**: Continuous improvement from user feedback
5. **Rich Feedback Loops**: Multi-level feedback on all AI outputs

## Core Principles

- **Audio is Source of Truth**: Text is a view on audio, not the truth itself
- **Corrections are First-Class**: Edits tracked, versioned, and used for learning
- **Context Improves Accuracy**: Use conversation context + audio for better transcription
- **User is Teacher**: Every correction trains the system
- **Confidence Throughout**: Show uncertainty everywhere AI makes decisions

---

## Extended Schema

### 1. Audio Segments

```sql
CREATE TABLE audio_segments (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    utterance_id UUID REFERENCES utterances(id) ON DELETE SET NULL,

    -- Storage
    gcs_path TEXT NOT NULL, -- Path to audio file in GCS
    storage_format TEXT DEFAULT 'webm', -- 'webm', 'wav', 'mp3', 'opus'
    duration_seconds FLOAT NOT NULL,

    -- Temporal
    timestamp_start FLOAT NOT NULL, -- Seconds from conversation start
    timestamp_end FLOAT NOT NULL,

    -- Audio Metadata
    sample_rate INTEGER, -- Hz
    channels INTEGER DEFAULT 1, -- Mono/stereo
    bitrate INTEGER, -- kbps
    file_size_bytes BIGINT,

    -- Processing
    transcribed_by TEXT[], -- ['assemblyai', 'whisper', 'user_corrected']
    transcription_version INTEGER DEFAULT 1, -- Incremented on re-transcription

    -- Quality
    audio_quality FLOAT, -- 0-1, signal quality
    has_noise BOOLEAN DEFAULT FALSE,
    has_overlap BOOLEAN DEFAULT FALSE, -- Multiple speakers talking

    -- Privacy
    is_redacted BOOLEAN DEFAULT FALSE, -- PII removed from audio
    redaction_metadata JSONB, -- Which segments were redacted

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_duration CHECK (timestamp_end > timestamp_start)
);

CREATE INDEX idx_audio_conversation ON audio_segments(conversation_id, timestamp_start);
CREATE INDEX idx_audio_utterance ON audio_segments(utterance_id);
CREATE INDEX idx_audio_quality ON audio_segments(conversation_id, audio_quality)
    WHERE audio_quality < 0.7; -- Index low-quality segments
```

### 2. Transcription Versions (Immutable Log)

```sql
CREATE TABLE transcription_versions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utterance_id UUID NOT NULL REFERENCES utterances(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Content
    text TEXT NOT NULL,
    text_normalized TEXT, -- Cleaned, normalized

    -- Source
    source_type TEXT NOT NULL, -- 'asr', 'user_correction', 'ai_inference', 'hybrid'
    source_provider TEXT, -- 'assemblyai', 'whisper', 'user_123', 'claude'
    source_confidence FLOAT, -- Overall confidence (0-1)

    -- Audio Reference
    audio_segment_id UUID REFERENCES audio_segments(id),

    -- Word-level Data
    word_timings JSONB[], -- [{word, start, end, confidence}]
    uncertain_words TEXT[], -- Words flagged as low confidence

    -- Context Used (for AI inference)
    context_used JSONB, -- {previous_utterances: [], next_utterances: [], topic_context: "..."}

    -- Changes from Previous Version
    previous_version_id UUID REFERENCES transcription_versions(id),
    edit_distance INTEGER, -- Levenshtein distance from previous
    changes JSONB, -- Detailed diff: [{type: 'insert', position: 5, text: 'hello'}]

    -- Feedback
    was_corrected BOOLEAN DEFAULT FALSE,
    correction_id UUID, -- References corrections table

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_utterance_version UNIQUE(utterance_id, version),
    CONSTRAINT valid_source CHECK (
        source_type IN ('asr', 'user_correction', 'ai_inference', 'hybrid')
    )
);

CREATE INDEX idx_transcription_utterance ON transcription_versions(utterance_id, version DESC);
CREATE INDEX idx_transcription_uncertain ON transcription_versions(utterance_id)
    WHERE array_length(uncertain_words, 1) > 0;
```

**Word Timing Schema:**
```json
{
  "word": "approximately",
  "start": 12.45,
  "end": 13.02,
  "confidence": 0.65,
  "alternatives": [
    {"word": "proximately", "confidence": 0.20},
    {"word": "appropriately", "confidence": 0.15}
  ]
}
```

### 3. User Corrections

```sql
CREATE TABLE corrections (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Target
    target_type TEXT NOT NULL, -- 'utterance', 'node', 'claim', 'speaker_name', 'timestamp'
    target_id UUID NOT NULL,

    -- Correction
    field_name TEXT NOT NULL, -- 'text', 'speaker_id', 'timestamp_start', 'node_name', etc.
    old_value TEXT NOT NULL,
    new_value TEXT NOT NULL,

    -- Context
    correction_reason TEXT, -- 'transcription_error', 'speaker_misattribution', 'timing_error', etc.
    user_comment TEXT, -- Optional explanation

    -- User
    user_id TEXT NOT NULL,
    user_confidence FLOAT DEFAULT 1.0, -- User's confidence in their correction

    -- Validation
    was_validated BOOLEAN, -- Other users agree?
    validation_count INTEGER DEFAULT 0,
    disagreement_count INTEGER DEFAULT 0,

    -- Impact
    affects_node_ids UUID[], -- Which nodes need reprocessing
    affects_claim_ids UUID[], -- Which claims need reprocessing
    reprocessing_triggered BOOLEAN DEFAULT FALSE,

    -- Learning
    was_used_for_training BOOLEAN DEFAULT FALSE,
    training_dataset_id TEXT, -- Which training dataset this was added to

    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ,

    CONSTRAINT valid_target_type CHECK (
        target_type IN ('utterance', 'node', 'claim', 'speaker_name', 'timestamp', 'relationship')
    ),
    CONSTRAINT valid_reason CHECK (
        correction_reason IN (
            'transcription_error', 'speaker_misattribution', 'timing_error',
            'topic_misidentification', 'claim_misclassification', 'other'
        )
    )
);

CREATE INDEX idx_corrections_target ON corrections(target_type, target_id);
CREATE INDEX idx_corrections_conversation ON corrections(conversation_id, created_at DESC);
CREATE INDEX idx_corrections_training ON corrections(was_used_for_training);
CREATE INDEX idx_corrections_pending_validation ON corrections(conversation_id)
    WHERE was_validated IS NULL;
```

### 4. AI Correction Suggestions

```sql
CREATE TABLE correction_suggestions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utterance_id UUID NOT NULL REFERENCES utterances(id) ON DELETE CASCADE,

    -- Suggestion
    field_name TEXT NOT NULL DEFAULT 'text',
    current_value TEXT NOT NULL,
    suggested_value TEXT NOT NULL,

    -- Confidence
    confidence FLOAT NOT NULL, -- 0-1
    model_name TEXT, -- Which model generated this
    model_version TEXT,

    -- Evidence
    evidence_type TEXT, -- 'context', 'audio_reanalysis', 'pattern', 'dictionary'
    evidence JSONB, -- Detailed explanation

    -- Context Window Used
    context_before TEXT[], -- Previous utterances
    context_after TEXT[], -- Following utterances
    topic_context TEXT, -- Current topic/node

    -- User Response
    user_action TEXT, -- 'accepted', 'rejected', 'modified', 'ignored'
    user_modified_to TEXT, -- If user modified the suggestion
    user_feedback TEXT, -- Why rejected/modified

    -- Learning Signal
    feedback_score FLOAT, -- -1 (bad) to +1 (good)

    created_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,

    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT valid_evidence CHECK (
        evidence_type IN ('context', 'audio_reanalysis', 'pattern', 'dictionary', 'hybrid')
    ),
    CONSTRAINT valid_action CHECK (
        user_action IS NULL OR
        user_action IN ('accepted', 'rejected', 'modified', 'ignored')
    )
);

CREATE INDEX idx_suggestions_utterance ON correction_suggestions(utterance_id);
CREATE INDEX idx_suggestions_pending ON correction_suggestions(utterance_id)
    WHERE user_action IS NULL AND confidence > 0.7;
CREATE INDEX idx_suggestions_feedback ON correction_suggestions(feedback_score)
    WHERE feedback_score IS NOT NULL;
```

**Evidence Schema (Context-based):**
```json
{
  "evidence_type": "context",
  "reasoning": "Given the surrounding conversation about API design, 'rest' should likely be 'REST'",
  "context_clues": [
    "Previous utterance mentioned 'GraphQL vs REST'",
    "Current node topic is 'API Architecture'",
    "Speaker has mentioned REST 3 times previously"
  ],
  "alternative_interpretations": [
    {"value": "rest", "confidence": 0.3, "meaning": "to rest/relax"}
  ]
}
```

**Evidence Schema (Audio reanalysis):**
```json
{
  "evidence_type": "audio_reanalysis",
  "reasoning": "Re-analyzed audio with Whisper v3, higher confidence in 'approximately' vs 'appropriately'",
  "audio_segment_id": "uuid",
  "reanalysis_model": "whisper-large-v3",
  "phonetic_match_score": 0.92,
  "acoustic_features": {
    "formant_f1": 450,
    "formant_f2": 1800,
    "duration_ms": 570
  }
}
```

### 5. Feedback Events (Rich, Multi-level)

```sql
CREATE TABLE feedback_events (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Target (what is being given feedback on)
    target_type TEXT NOT NULL,
    target_id UUID NOT NULL,

    -- Feedback Type
    feedback_type TEXT NOT NULL, -- 'rating', 'correction', 'flag', 'comment', 'reaction'

    -- Rating Feedback
    rating_value FLOAT, -- 1-5 or 0-1 depending on scale
    rating_dimension TEXT, -- 'accuracy', 'relevance', 'completeness', 'clarity'

    -- Flag Feedback
    flag_reason TEXT, -- 'inaccurate', 'offensive', 'irrelevant', 'bug', 'inappropriate'
    flag_severity TEXT, -- 'low', 'medium', 'high', 'critical'

    -- Comment Feedback
    comment_text TEXT,

    -- Reaction Feedback (quick emoji-style)
    reaction_type TEXT, -- 'thumbs_up', 'thumbs_down', 'helpful', 'not_helpful', 'insightful', 'wrong'

    -- User
    user_id TEXT NOT NULL,

    -- Context
    session_id UUID, -- Which viewing session
    user_state JSONB, -- What was user doing when they gave feedback

    -- Response
    was_actioned BOOLEAN DEFAULT FALSE,
    action_taken TEXT,
    action_taken_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_target CHECK (
        target_type IN (
            'utterance', 'node', 'claim', 'relationship', 'speaker_analytics',
            'correction_suggestion', 'thread_suggestion', 'crux', 'goal_progress'
        )
    ),
    CONSTRAINT valid_feedback_type CHECK (
        feedback_type IN ('rating', 'correction', 'flag', 'comment', 'reaction')
    )
);

CREATE INDEX idx_feedback_target ON feedback_events(target_type, target_id);
CREATE INDEX idx_feedback_conversation ON feedback_events(conversation_id, created_at DESC);
CREATE INDEX idx_feedback_actionable ON feedback_events(was_actioned)
    WHERE flag_severity IN ('high', 'critical') AND was_actioned = FALSE;
```

### 6. Learning Dataset (For Model Fine-tuning)

```sql
CREATE TABLE training_examples (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Example Type
    example_type TEXT NOT NULL, -- 'transcription', 'segmentation', 'claim_classification', 'speaker_attribution'

    -- Input
    input_data JSONB NOT NULL,

    -- Ground Truth (from user corrections)
    ground_truth JSONB NOT NULL,

    -- Original Prediction
    model_prediction JSONB,
    prediction_confidence FLOAT,

    -- Source
    source_correction_id UUID REFERENCES corrections(id),
    conversation_id UUID REFERENCES conversations(id),

    -- Quality
    example_quality_score FLOAT, -- Human-assessed quality (0-1)
    is_validated BOOLEAN DEFAULT FALSE,

    -- Usage
    used_in_training BOOLEAN DEFAULT FALSE,
    training_run_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_example_type CHECK (
        example_type IN (
            'transcription', 'segmentation', 'claim_classification',
            'speaker_attribution', 'relationship_detection', 'topic_detection'
        )
    )
);

CREATE INDEX idx_training_type ON training_examples(example_type);
CREATE INDEX idx_training_quality ON training_examples(example_quality_score DESC)
    WHERE is_validated = TRUE AND used_in_training = FALSE;
```

**Training Example Schema (Transcription):**
```json
{
  "example_type": "transcription",
  "input_data": {
    "audio_segment_id": "uuid",
    "audio_features": {...},
    "context_before": ["previous utterance text"],
    "context_after": ["next utterance text"],
    "topic": "API Design Discussion",
    "speaker_history": ["REST", "GraphQL", "endpoints"]
  },
  "ground_truth": {
    "text": "We should use REST for simplicity",
    "confidence": 1.0,
    "source": "user_correction"
  },
  "model_prediction": {
    "text": "We should use rest for simplicity",
    "confidence": 0.85,
    "model": "assemblyai"
  }
}
```

---

## Correction Workflows

### Workflow 1: User Corrects Transcription Error

```sql
-- User clicks on utterance, edits "rest" → "REST"
BEGIN;

-- 1. Create correction record
INSERT INTO corrections (
    target_type, target_id, field_name,
    old_value, new_value, correction_reason,
    user_id, user_confidence
) VALUES (
    'utterance', utterance_uuid, 'text',
    'We should use rest for simplicity',
    'We should use REST for simplicity',
    'transcription_error',
    'user_123', 1.0
) RETURNING id INTO correction_id;

-- 2. Create new transcription version
INSERT INTO transcription_versions (
    utterance_id, version, text, source_type,
    source_provider, source_confidence, previous_version_id,
    was_corrected, correction_id
)
SELECT
    utterance_uuid,
    (SELECT MAX(version) + 1 FROM transcription_versions WHERE utterance_id = utterance_uuid),
    'We should use REST for simplicity',
    'user_correction',
    'user_123',
    1.0,
    (SELECT id FROM transcription_versions WHERE utterance_id = utterance_uuid ORDER BY version DESC LIMIT 1),
    TRUE,
    correction_id
FROM corrections WHERE id = correction_id;

-- 3. Update current utterance text
UPDATE utterances
SET text = 'We should use REST for simplicity',
    updated_at = NOW()
WHERE id = utterance_uuid;

-- 4. Create training example
INSERT INTO training_examples (
    example_type, input_data, ground_truth,
    model_prediction, source_correction_id, conversation_id
) VALUES (
    'transcription',
    jsonb_build_object(
        'audio_segment_id', (SELECT audio_segment_id FROM audio_segments WHERE utterance_id = utterance_uuid),
        'context_before', (SELECT array_agg(text) FROM utterances WHERE conversation_id = conv_id AND sequence_number < utt_seq ORDER BY sequence_number DESC LIMIT 3),
        'context_after', (SELECT array_agg(text) FROM utterances WHERE conversation_id = conv_id AND sequence_number > utt_seq ORDER BY sequence_number LIMIT 3)
    ),
    jsonb_build_object('text', 'We should use REST for simplicity'),
    jsonb_build_object('text', 'We should use rest for simplicity'),
    correction_id,
    conv_id
);

-- 5. Trigger reprocessing of affected nodes (if text change is significant)
UPDATE corrections
SET affects_node_ids = (
    SELECT array_agg(DISTINCT node_id)
    FROM utterances
    WHERE id = utterance_uuid AND node_id IS NOT NULL
);

COMMIT;
```

### Workflow 2: AI Suggests Context-Based Correction

```python
# Application-level logic
def suggest_corrections_for_utterance(utterance_id):
    """
    Analyze utterance for potential errors using context + audio
    """
    utterance = db.get_utterance(utterance_id)

    # Get context window
    context_before = db.get_utterances_before(utterance_id, limit=5)
    context_after = db.get_utterances_after(utterance_id, limit=5)
    current_node = db.get_node_for_utterance(utterance_id)

    # Build prompt for LLM
    prompt = f"""
    Given this conversation context, check if the transcription is likely accurate:

    Previous utterances:
    {format_utterances(context_before)}

    CURRENT (to check): {utterance.text}

    Following utterances:
    {format_utterances(context_after)}

    Current topic: {current_node.node_name if current_node else "Unknown"}
    Speaker: {utterance.speaker_name}

    Analyze for:
    1. Homonyms (e.g., "rest" vs "REST" in technical context)
    2. Missing capitalization (proper nouns, acronyms)
    3. Technical terms likely misheard
    4. Context-inappropriate words

    If you find likely errors, suggest corrections with confidence (0-1).
    """

    suggestions = llm.generate(prompt, model="claude-3-haiku")

    # Also: Re-analyze audio with different model if low confidence
    if utterance.transcription_confidence < 0.7:
        audio_segment = db.get_audio_segment(utterance.id)
        whisper_transcription = whisper.transcribe(audio_segment.gcs_path)

        if whisper_transcription != utterance.text:
            suggestions.append({
                'suggested_value': whisper_transcription,
                'confidence': whisper_confidence,
                'evidence_type': 'audio_reanalysis'
            })

    # Store suggestions
    for suggestion in suggestions:
        db.insert_correction_suggestion(
            utterance_id=utterance_id,
            current_value=utterance.text,
            suggested_value=suggestion['suggested_value'],
            confidence=suggestion['confidence'],
            evidence_type=suggestion['evidence_type'],
            evidence=suggestion['evidence'],
            context_before=[u.text for u in context_before],
            context_after=[u.text for u in context_after]
        )

    return suggestions
```

### Workflow 3: Online Learning from Corrections

```python
# Background job: Batch process corrections into training data
def create_training_batch():
    """
    Collect recent corrections and prepare for model fine-tuning
    """
    # Get unprocessed corrections with high confidence
    corrections = db.query("""
        SELECT c.*, u.*, tv.text as original_transcription
        FROM corrections c
        JOIN utterances u ON c.target_id = u.id
        JOIN transcription_versions tv ON tv.utterance_id = u.id AND tv.version = 1
        WHERE c.target_type = 'utterance'
          AND c.user_confidence > 0.8
          AND c.was_used_for_training = FALSE
          AND c.created_at > NOW() - INTERVAL '7 days'
        LIMIT 1000
    """)

    training_examples = []
    for correction in corrections:
        # Fetch audio and context
        audio_segment = get_audio_segment(correction.utterance_id)
        context = get_context_window(correction.utterance_id)

        example = {
            'audio_path': audio_segment.gcs_path,
            'audio_features': extract_features(audio_segment),
            'context_text': context,
            'original_prediction': correction.old_value,
            'ground_truth': correction.new_value,
            'metadata': {
                'speaker_id': correction.speaker_id,
                'topic': get_node_topic(correction.utterance_id),
                'conversation_type': get_conversation_type(correction.conversation_id)
            }
        }
        training_examples.append(example)

        # Mark as used
        db.execute("""
            UPDATE corrections
            SET was_used_for_training = TRUE,
                training_dataset_id = ?
            WHERE id = ?
        """, [dataset_id, correction.id])

    # Save training dataset
    save_training_dataset(training_examples, dataset_id='batch_2025_11_10')

    # Optionally: Trigger fine-tuning job
    # finetune_model(dataset_id='batch_2025_11_10')
```

### Workflow 4: Collaborative Validation

```sql
-- User A makes correction
-- System notifies User B who was in the conversation
-- User B validates or disputes

-- Validate correction
UPDATE corrections
SET validation_count = validation_count + 1,
    was_validated = CASE
        WHEN validation_count + 1 >= 2 THEN TRUE
        ELSE was_validated
    END
WHERE id = correction_id;

-- Dispute correction
UPDATE corrections
SET disagreement_count = disagreement_count + 1
WHERE id = correction_id;

-- If disputed, flag for manual review
INSERT INTO feedback_events (
    target_type, target_id, feedback_type,
    flag_reason, flag_severity, user_id
)
SELECT
    'correction', id, 'flag',
    'disputed_correction', 'medium', 'user_456'
FROM corrections
WHERE id = correction_id AND disagreement_count >= 2;
```

---

## UI Components

### 1. Correction Interface

```jsx
// UtteranceEditor.jsx
function UtteranceEditor({ utterance }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(utterance.text);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    // Fetch AI suggestions for this utterance
    fetchCorrectionSuggestions(utterance.id).then(setSuggestions);
  }, [utterance.id]);

  const handleSave = () => {
    submitCorrection({
      target_id: utterance.id,
      old_value: utterance.text,
      new_value: editedText,
      correction_reason: 'transcription_error'
    });
    setIsEditing(false);
  };

  return (
    <div className="utterance-container">
      {/* Show word-level confidence */}
      <div className="utterance-text">
        {utterance.word_timings?.map((word, idx) => (
          <span
            key={idx}
            className={word.confidence < 0.7 ? 'low-confidence' : ''}
            title={`Confidence: ${word.confidence}`}
          >
            {word.word}{' '}
          </span>
        ))}
      </div>

      {/* Show AI suggestions */}
      {suggestions.length > 0 && (
        <div className="suggestions">
          <h4>Possible corrections:</h4>
          {suggestions.map(sugg => (
            <SuggestionCard
              key={sugg.id}
              suggestion={sugg}
              onAccept={() => applySuggestion(sugg)}
              onReject={() => rejectSuggestion(sugg)}
            />
          ))}
        </div>
      )}

      {/* Edit mode */}
      {isEditing ? (
        <textarea value={editedText} onChange={(e) => setEditedText(e.target.value)} />
      ) : (
        <button onClick={() => setIsEditing(true)}>Edit</button>
      )}

      {/* Audio playback */}
      <AudioPlayer
        audioSegmentId={utterance.audio_segment_id}
        start={utterance.timestamp_start}
        end={utterance.timestamp_end}
      />
    </div>
  );
}
```

### 2. Feedback Buttons

```jsx
// FeedbackButtons.jsx
function FeedbackButtons({ targetType, targetId }) {
  return (
    <div className="feedback-buttons">
      <button onClick={() => submitFeedback('thumbs_up')}>👍</button>
      <button onClick={() => submitFeedback('thumbs_down')}>👎</button>
      <button onClick={() => submitFeedback('insightful')}>💡</button>
      <button onClick={() => submitFeedback('wrong')}>❌</button>
      <button onClick={() => openFlagDialog()}>🚩 Flag</button>
      <button onClick={() => openCommentDialog()}>💬 Comment</button>
    </div>
  );
}

// Can be attached to any AI output: nodes, claims, suggestions, etc.
```

### 3. Confidence Indicators

```jsx
// ConfidenceIndicator.jsx
function ConfidenceIndicator({ confidence, showTooltip = true }) {
  const color = confidence > 0.8 ? 'green' :
                confidence > 0.6 ? 'yellow' : 'red';

  return (
    <span
      className={`confidence-badge confidence-${color}`}
      title={showTooltip ? `Confidence: ${(confidence * 100).toFixed(0)}%` : undefined}
    >
      {confidence > 0.8 ? '●' : confidence > 0.6 ? '◐' : '○'}
    </span>
  );
}

// Usage:
<ConfidenceIndicator confidence={node.confidence_score} />
<ConfidenceIndicator confidence={claim.classification_confidence} />
```

---

## API Endpoints

### Submit Correction
```
POST /corrections/

Body:
{
  "target_type": "utterance",
  "target_id": "uuid",
  "field_name": "text",
  "old_value": "rest",
  "new_value": "REST",
  "correction_reason": "transcription_error",
  "user_comment": "Technical term, should be capitalized"
}

Response:
{
  "correction_id": "uuid",
  "affects_nodes": ["uuid1", "uuid2"],
  "reprocessing_triggered": true,
  "training_example_created": true
}
```

### Get Correction Suggestions
```
GET /utterances/{id}/correction-suggestions

Response:
{
  "suggestions": [
    {
      "id": "uuid",
      "suggested_value": "REST",
      "confidence": 0.92,
      "evidence_type": "context",
      "evidence": {
        "reasoning": "Technical context suggests REST API, not 'rest'"
      }
    }
  ]
}
```

### Submit Feedback
```
POST /feedback/

Body:
{
  "target_type": "claim",
  "target_id": "uuid",
  "feedback_type": "rating",
  "rating_value": 4,
  "rating_dimension": "accuracy",
  "comment_text": "Claim is mostly accurate but missing nuance"
}
```

### Get Audio Segment
```
GET /audio/{utterance_id}

Response:
{
  "audio_url": "https://storage.googleapis.com/...",
  "format": "webm",
  "duration": 3.5,
  "timestamp_start": 125.4,
  "timestamp_end": 128.9
}
```

### Re-transcribe with Different Model
```
POST /utterances/{id}/retranscribe

Body:
{
  "model": "whisper-large-v3",
  "use_context": true
}

Response:
{
  "new_version": 3,
  "text": "We should use REST for simplicity",
  "confidence": 0.95,
  "changes_from_previous": [
    {"position": 14, "type": "replace", "old": "rest", "new": "REST"}
  ]
}
```

---

## Metrics & Monitoring

### Correction Rate
```sql
-- Percentage of utterances corrected
SELECT
    c.conversation_id,
    COUNT(DISTINCT c.target_id) * 100.0 / (SELECT COUNT(*) FROM utterances WHERE conversation_id = c.conversation_id) AS correction_rate
FROM corrections c
WHERE c.target_type = 'utterance'
GROUP BY c.conversation_id;
```

### Suggestion Acceptance Rate
```sql
-- How often users accept AI suggestions
SELECT
    model_name,
    COUNT(*) FILTER (WHERE user_action = 'accepted') * 100.0 / COUNT(*) AS acceptance_rate
FROM correction_suggestions
WHERE user_action IS NOT NULL
GROUP BY model_name;
```

### Training Data Growth
```sql
-- New training examples per day
SELECT
    DATE(created_at) AS date,
    example_type,
    COUNT(*) AS examples_created
FROM training_examples
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY date, example_type
ORDER BY date DESC;
```

### Transcription Quality Over Time
```sql
-- Average confidence and correction rate over time
SELECT
    DATE_TRUNC('week', u.created_at) AS week,
    AVG(tv.source_confidence) AS avg_confidence,
    COUNT(DISTINCT c.id) * 100.0 / COUNT(DISTINCT u.id) AS correction_rate
FROM utterances u
JOIN transcription_versions tv ON tv.utterance_id = u.id AND tv.version = 1
LEFT JOIN corrections c ON c.target_id = u.id AND c.target_type = 'utterance'
GROUP BY week
ORDER BY week DESC;
```

---

## Privacy & Ethics

### Audio Data Retention
```sql
-- Delete audio after N days (configurable per user)
DELETE FROM audio_segments
WHERE conversation_id IN (
    SELECT id FROM conversations
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND owner_id IN (SELECT id FROM users WHERE audio_retention_days = 90)
);

-- Or anonymize: keep audio but delete speaker attribution
UPDATE audio_segments
SET speaker_metadata = NULL
WHERE conversation_id IN (SELECT id FROM conversations WHERE anonymize_after_days < EXTRACT(DAY FROM NOW() - created_at));
```

### Correction Privacy
- Corrections are attributed to users (for quality/trust)
- Option to make corrections anonymous in shared conversations
- Training examples strip PII before inclusion in datasets

---

## Next Steps

1. **Prototype Correction UI**: Build simple correction interface
2. **Audio Storage**: Implement audio segment storage in GCS
3. **Suggestion Engine**: Build context-aware correction suggestion system
4. **Training Pipeline**: Set up automated training data collection
5. **A/B Test**: Compare correction rate with/without AI suggestions
6. **Fine-tune Model**: Train custom transcription model on collected corrections

---

## Open Questions

1. **Audio Retention**: How long to keep audio? Different policies for different users?
2. **Re-processing**: Auto-trigger node/claim reprocessing on significant corrections, or manual?
3. **Suggestion Frequency**: How many suggestions per utterance? Don't overwhelm user.
4. **Training Frequency**: Daily? Weekly? On-demand when N new examples collected?
5. **Model Choice**: Fine-tune Whisper? Train custom ASR? Use correction data for LLM?
6. **Collaborative Corrections**: Allow multiple users to suggest corrections? Voting system?
