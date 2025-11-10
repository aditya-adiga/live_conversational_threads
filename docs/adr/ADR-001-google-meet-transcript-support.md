# ADR-001: Add Support for Google Meet Transcripts with Speaker Diarization

**Status**: Proposed
**Date**: 2025-11-10
**Deciders**: Development Team
**Technical Story**: Support async data sources (Google Meet recordings) alongside live audio streaming

## Context and Problem Statement

The Live Conversational Threads (LCT) application currently only supports real-time audio streaming through WebSocket connections. This architecture:

1. **Loses speaker attribution**: Audio is converted to text without preserving who said what
2. **Requires live participation**: Users must be present during the conversation to capture it
3. **Cannot process existing recordings**: No way to analyze past meetings or conversations
4. **Lacks multi-speaker awareness**: Graph generation doesn't understand dialogue dynamics

**User Need**: Process Google Meet recordings/transcripts where speaker diarization has already been performed, preserving speaker information throughout the analysis pipeline.

## Decision Drivers

1. **Speaker Attribution is Critical**: Understanding who said what is essential for meaningful conversation analysis
2. **Async vs Real-time**: Need to support both live streaming and pre-recorded transcripts
3. **Data Quality**: Google Meet provides high-quality speaker-diarized transcripts
4. **User Workflow**: Many users want to analyze past meetings, not just live conversations
5. **Minimal Breaking Changes**: Should not disrupt existing live audio functionality

## Considered Options

### Option 1: Extend Existing Architecture (Recommended)
Add parallel processing path for pre-recorded transcripts alongside existing live streaming.

**Pros:**
- Preserves existing live audio functionality
- Clear separation of concerns
- Can optimize each path independently
- Gradual migration path

**Cons:**
- More code to maintain
- Some duplication in processing logic
- Need to keep two paths in sync

### Option 2: Replace Live Streaming with Unified Pipeline
Refactor to treat live audio as "streaming transcript" input.

**Pros:**
- Single code path
- Easier maintenance long-term
- Consistent behavior

**Cons:**
- Major breaking changes
- Risk of disrupting working live feature
- Complex refactoring effort
- Potentially worse performance for live streaming

### Option 3: Separate Service for Transcript Processing
Create microservice specifically for transcript analysis.

**Pros:**
- Complete separation
- Independent scaling
- Technology flexibility

**Cons:**
- Infrastructure complexity
- Data synchronization challenges
- Overhead of service communication
- May be over-engineering

## Decision Outcome

**Chosen option: Option 1 - Extend Existing Architecture**

We will add a parallel processing path for pre-recorded transcripts while maintaining the existing live audio streaming functionality.

### Architecture Changes

#### 1. Data Model Extensions

**Add Speaker Information to Nodes:**
```python
class ConversationNode:
    node_name: str
    type: str
    predecessor: Optional[str]
    successor: Optional[str]
    chunk_id: Optional[str]
    is_bookmark: bool
    is_contextual_progress: bool
    summary: str
    claims: List[str]
    contextual_relation: Dict[str, str]
    linked_nodes: List[str]

    # NEW FIELDS
    speaker_info: Optional[SpeakerInfo]  # Speaker attribution
    speaker_transitions: List[SpeakerTransition]  # Speaker changes within node
    dialogue_type: Optional[str]  # monologue, dialogue, multi-party
```

**Speaker Information Schema:**
```python
class SpeakerInfo:
    primary_speaker: str  # Main speaker for this node
    speaker_name: Optional[str]  # Human-readable name
    speaker_id: str  # Unique identifier
    contribution_percentage: float  # % of node content from this speaker

class SpeakerTransition:
    from_speaker: str
    to_speaker: str
    position: int  # Character position in chunk
    context: str  # Brief context of transition
```

**Extended Chunk Format:**
```python
class TranscriptChunk:
    chunk_id: str
    text: str

    # NEW FIELDS
    utterances: List[Utterance]  # Speaker-attributed segments
    speakers_present: List[str]  # All speakers in this chunk
    dominant_speaker: Optional[str]  # Primary speaker if applicable

class Utterance:
    speaker_id: str
    speaker_name: Optional[str]
    text: str
    start_time: Optional[float]  # Timestamp if available
    end_time: Optional[float]
    position: int  # Order in conversation
```

#### 2. New API Endpoints

**Import Google Meet Transcript:**
```
POST /import/google-meet-transcript/

Request:
{
  "source_type": "google_doc" | "text" | "url",
  "source_data": "...",  // URL, doc ID, or raw text
  "file_name": "Team Standup 2025-11-10",
  "preserve_speaker_info": true,
  "speaker_mapping": {  // Optional human-readable names
    "Speaker 1": "Alice Chen",
    "Speaker 2": "Bob Smith"
  }
}

Response:
{
  "conversation_id": "uuid",
  "file_name": "...",
  "speakers_detected": ["Speaker 1", "Speaker 2"],
  "no_of_nodes": 15,
  "utterance_count": 143
}
```

**Import Generic Diarized Transcript:**
```
POST /import/diarized-transcript/

Request:
{
  "format": "json" | "txt" | "vtt" | "srt",
  "transcript_data": "...",
  "file_name": "...",
  "timestamp_format": "seconds" | "timecode"
}
```

**Get Speaker Analytics:**
```
GET /conversations/{conversation_id}/speaker-analytics

Response:
{
  "speakers": [
    {
      "speaker_id": "Speaker 1",
      "speaker_name": "Alice Chen",
      "total_utterances": 45,
      "total_words": 1234,
      "participation_percentage": 35.5,
      "topics_led": ["Feature Planning", "Technical Architecture"],
      "interaction_partners": ["Speaker 2", "Speaker 3"]
    }
  ],
  "speaker_interactions": [
    {
      "speaker_pair": ["Speaker 1", "Speaker 2"],
      "interaction_count": 23,
      "topics": ["API Design", "Database Schema"]
    }
  ]
}
```

#### 3. Processing Pipeline Changes

**Current Pipeline (Live Audio):**
```
Audio Stream → AssemblyAI → Text Chunks → LLM Processing → Nodes → GCS/DB
```

**New Pipeline (Pre-recorded Transcript):**
```
Transcript Source → Parser → Utterances → Speaker-Aware Chunking →
  LLM Processing (speaker-aware) → Nodes with Speaker Info → GCS/DB
```

**Shared Components:**
- LLM processing (with speaker context awareness)
- GCS storage
- Database operations
- Graph generation
- Visualization

**New Components:**
- Transcript parser (multiple format support)
- Speaker-aware chunking algorithm
- Google Doc API integration
- Speaker analytics engine

#### 4. Frontend Changes

**New UI Components:**
- `ImportTranscript.jsx` - Upload/import transcript files or Google Doc URLs
- `SpeakerAnalytics.jsx` - Visualize speaker participation and interactions
- `SpeakerLegend.jsx` - Show speaker color coding in graphs
- `SpeakerFilter.jsx` - Filter nodes by speaker

**Enhanced Graph Visualizations:**
- Color-code nodes by primary speaker
- Show speaker transitions as node borders/patterns
- Display speaker icons/avatars on nodes
- Filter graph by speaker or speaker interactions
- Highlight dialogue patterns (back-and-forth, monologues)

**New Page:**
- `ImportTranscriptPage.jsx` - Dedicated page for transcript import with format selection

#### 5. LLM Prompt Engineering

**Updated System Prompt (excerpt):**
```
You are analyzing a multi-speaker conversation transcript. Each utterance is
attributed to a speaker. When creating conversation nodes:

1. Track the PRIMARY SPEAKER for each node (who contributed most content)
2. Note SPEAKER TRANSITIONS when the dominant speaker changes within a topic
3. Identify DIALOGUE PATTERNS:
   - Monologue: Single speaker dominates (>80%)
   - Dialogue: Two speakers alternating frequently
   - Multi-party: Three or more speakers contributing
4. Create contextual relationships that capture:
   - Agreement/disagreement between speakers
   - Question-answer pairs
   - Building on others' ideas
5. Flag SPEAKER-SPECIFIC INSIGHTS:
   - Is this a bookmark because of WHO said it?
   - Does this represent a particular speaker's expertise area?

Input format:
[Speaker 1]: First utterance text
[Speaker 2]: Response text
...
```

## Consequences

### Positive

1. **Richer Analysis**: Speaker attribution enables deeper conversation insights
2. **Broader Use Cases**: Support both live and async workflows
3. **Better User Experience**: Users can analyze past meetings
4. **Enhanced Visualizations**: Speaker-aware graphs reveal dialogue dynamics
5. **Future Extensibility**: Foundation for speaker analytics, sentiment by speaker, etc.
6. **Google Meet Integration**: Direct support for common enterprise tool

### Negative

1. **Data Model Complexity**: Nodes and chunks become more complex
2. **Storage Overhead**: Additional speaker metadata increases storage needs (~15-25%)
3. **Migration Required**: Existing conversations lack speaker info (backward compatibility needed)
4. **Maintenance Burden**: Two processing paths to maintain
5. **Testing Complexity**: Need test data for both live and transcript modes

### Neutral

1. **Performance Impact**: Minimal for live streaming (unchanged), transcript processing is inherently batch
2. **LLM Token Usage**: Slightly higher due to speaker attribution in prompts (~10-15% increase)
3. **UI Complexity**: More visualization options but optional for users who don't need them

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Extend data models (Node, Chunk schemas)
- [ ] Update database schema with speaker fields
- [ ] Create migration script for backward compatibility
- [ ] Add speaker fields to Pydantic models

### Phase 2: Backend - Transcript Import (Week 2)
- [ ] Implement transcript parser (support plain text, JSON, VTT, SRT)
- [ ] Add Google Doc API integration
- [ ] Create speaker-aware chunking algorithm
- [ ] Implement `/import/google-meet-transcript/` endpoint
- [ ] Implement `/import/diarized-transcript/` endpoint

### Phase 3: Backend - Speaker-Aware Processing (Week 2-3)
- [ ] Update LLM prompts for speaker awareness
- [ ] Modify `generate_lct_json_claude()` to handle speaker info
- [ ] Implement speaker analytics engine
- [ ] Add `/conversations/{id}/speaker-analytics` endpoint
- [ ] Update save/load functions to handle speaker metadata

### Phase 4: Frontend - Import UI (Week 3)
- [ ] Create `ImportTranscript.jsx` component
- [ ] Add transcript import page
- [ ] Support file upload (TXT, JSON, VTT, SRT)
- [ ] Support Google Doc URL input
- [ ] Add speaker name mapping UI

### Phase 5: Frontend - Speaker Visualization (Week 4)
- [ ] Add speaker color coding to graph nodes
- [ ] Create `SpeakerLegend.jsx` component
- [ ] Implement speaker filter controls
- [ ] Show speaker transitions in node details
- [ ] Create `SpeakerAnalytics.jsx` dashboard

### Phase 6: Testing & Documentation (Week 4)
- [ ] Unit tests for parsers and chunking
- [ ] Integration tests for import endpoints
- [ ] End-to-end tests with sample Meet transcripts
- [ ] Update API documentation
- [ ] Create user guide for transcript import
- [ ] Performance testing with large transcripts

### Phase 7: Canvas Integration (Week 5)
- [ ] Update Canvas export to include speaker info
- [ ] Add speaker colors to Canvas nodes
- [ ] Update Canvas import to parse speaker metadata
- [ ] Extend OBSIDIAN_CANVAS_INTEROP.md documentation

## Compliance and Security

### Google Doc Access
- **Authentication**: Use OAuth 2.0 for Google API access
- **Permissions**: Request minimal scopes (read-only document access)
- **Privacy**: Never store Google credentials; use token-based auth
- **Data Handling**: Transcript data treated same as audio transcripts (stored in GCS)

### Speaker Privacy
- **PII Considerations**: Speaker names may be PII
- **Anonymization Option**: Allow users to anonymize speaker names
- **Data Retention**: Follow same policies as existing conversations
- **Export Controls**: Include speaker info in data exports only if user opts in

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Google API rate limits | Medium | Medium | Implement caching, retry logic, quotas |
| Transcript format variations | High | Medium | Support multiple formats, robust parsing |
| Speaker misattribution in source | Medium | High | Allow manual correction, show confidence |
| Performance with large transcripts | Medium | Medium | Implement streaming processing, pagination |
| Breaking changes to existing features | Low | High | Comprehensive testing, feature flags |
| Storage cost increase | Medium | Low | Monitor usage, implement retention policies |

## Success Metrics

1. **Adoption**: 40%+ of conversations use transcript import within 3 months
2. **Accuracy**: Speaker attribution preserved with >95% accuracy through pipeline
3. **Performance**: Import 10,000 word transcript in <30 seconds
4. **User Satisfaction**: Positive feedback on speaker analytics features
5. **Compatibility**: 100% backward compatibility with existing conversations

## Related Decisions

- ADR-002: Google Meet Transcript Format Specification (to be written)
- ADR-003: Speaker Privacy and Anonymization (to be written)

## References

- [Google Meet API Documentation](https://developers.google.com/meet)
- [Google Docs API](https://developers.google.com/docs/api)
- [WebVTT Specification](https://www.w3.org/TR/webvtt1/)
- [SRT Subtitle Format](https://en.wikipedia.org/wiki/SubRip)
- [Speaker Diarization Research](https://arxiv.org/abs/2012.01477)

## Open Questions

1. **Format Priority**: Which transcript formats should we support first? (Google Doc, plain text, VTT?)
2. **Speaker Anonymization**: Should this be default or opt-in?
3. **Real-time Diarization**: Should we add live speaker diarization to audio streaming?
4. **Speaker Identification**: Support automatic speaker identification beyond "Speaker 1, 2, 3"?
5. **Multi-language**: How to handle speaker diarization in non-English transcripts?
6. **Historical Migration**: Should we attempt to add speaker info to old conversations?

## Appendix A: Example Transcript Formats

### Google Meet Export Format
```
Speaker 1: Hello everyone, let's start with the sprint planning.
Speaker 2: Sounds good. I want to discuss the API redesign first.
Speaker 1: Sure, Bob. What are your main concerns?
Speaker 2: Well, I think we should consider GraphQL instead of REST...
```

### VTT Format
```
WEBVTT

00:00:01.000 --> 00:00:05.000
<v Speaker 1>Hello everyone, let's start with the sprint planning.</v>

00:00:05.500 --> 00:00:09.000
<v Speaker 2>Sounds good. I want to discuss the API redesign first.</v>
```

### JSON Format (Structured)
```json
{
  "transcript": {
    "utterances": [
      {
        "speaker": "Speaker 1",
        "speaker_name": "Alice Chen",
        "text": "Hello everyone, let's start with the sprint planning.",
        "start_time": 1.0,
        "end_time": 5.0
      },
      {
        "speaker": "Speaker 2",
        "speaker_name": "Bob Smith",
        "text": "Sounds good. I want to discuss the API redesign first.",
        "start_time": 5.5,
        "end_time": 9.0
      }
    ]
  }
}
```

## Appendix B: Database Schema Changes

```sql
-- Add speaker information to nodes
ALTER TABLE conversation_nodes ADD COLUMN speaker_info JSONB;
ALTER TABLE conversation_nodes ADD COLUMN speaker_transitions JSONB[];
ALTER TABLE conversation_nodes ADD COLUMN dialogue_type VARCHAR(50);

-- Create speaker analytics table
CREATE TABLE speaker_analytics (
    conversation_id TEXT REFERENCES conversations(id),
    speaker_id TEXT NOT NULL,
    speaker_name TEXT,
    utterance_count INTEGER,
    word_count INTEGER,
    participation_percentage FLOAT,
    topics_led JSONB,
    PRIMARY KEY (conversation_id, speaker_id)
);

-- Create speaker interactions table
CREATE TABLE speaker_interactions (
    conversation_id TEXT REFERENCES conversations(id),
    speaker_1 TEXT NOT NULL,
    speaker_2 TEXT NOT NULL,
    interaction_count INTEGER,
    topics JSONB,
    PRIMARY KEY (conversation_id, speaker_1, speaker_2)
);
```

## Appendix C: Backward Compatibility Strategy

**Handling Existing Conversations:**

1. **Graceful Degradation**: Nodes without speaker info display normally
2. **Optional Features**: Speaker filters/analytics only show when speaker data present
3. **Migration Path**: Provide tool to re-process old conversations with speaker attribution (if original audio/transcript available)
4. **UI Indicators**: Show badge/icon indicating "speaker-aware" vs "legacy" conversations
5. **Default Values**: Null speaker fields for backward compatibility

**Code Example:**
```python
def get_primary_speaker(node: dict) -> Optional[str]:
    """Safely get primary speaker, handling legacy nodes."""
    if "speaker_info" not in node or node["speaker_info"] is None:
        return None
    return node["speaker_info"].get("primary_speaker")
```
