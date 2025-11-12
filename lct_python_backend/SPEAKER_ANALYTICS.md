# Speaker Analytics (Week 8)

## Overview

The **Speaker Analytics** system provides comprehensive statistical analysis of conversation participants, including time spoken, turn distribution, role detection, and topic dominance analysis. This feature helps users understand conversation dynamics, identify patterns, and analyze participant engagement.

### Key Features

1. **Time Spoken Analysis**: Calculate total time and percentage spoken by each participant
2. **Turn Distribution**: Count and analyze conversation turns per speaker
3. **Role Detection**: Automatically classify speakers as facilitator, contributor, or observer
4. **Topic Dominance**: Identify which topics each speaker dominated
5. **Timeline Visualization**: Chronological view of speaker activity
6. **Speaker Comparison**: Compare multiple speakers across various metrics

---

## Architecture

### Backend Components

```
lct_python_backend/
├── services/
│   └── speaker_analytics.py      # Analytics calculation service
├── analytics_api.py               # API router (optional/future)
└── backend.py                      # Analytics endpoints integrated here
```

### Frontend Components

```
lct_app/src/
├── services/
│   └── analyticsApi.js            # Analytics API client
├── pages/
│   └── Analytics.jsx              # Main analytics page
└── routes/
    └── AppRoutes.jsx              # Route: /analytics/:conversationId
```

---

## Backend Implementation

### SpeakerAnalytics Service

Located in `services/speaker_analytics.py`, this service calculates all speaker statistics.

#### Main Method

```python
async def calculate_full_analytics(self, conversation_id: str) -> Dict[str, Any]
```

**Returns:**
```python
{
    "speakers": {
        "speaker_id_1": {
            "speaker_id": str,
            "speaker_name": str,
            "time_spoken_seconds": float,
            "time_spoken_percentage": float,
            "turn_count": int,
            "turn_percentage": float,
            "topics_dominated": List[str],
            "role": str,  # "facilitator", "contributor", "observer"
            "avg_turn_duration": float
        },
        ...
    },
    "timeline": [
        {
            "sequence_number": int,
            "speaker_id": str,
            "speaker_name": str,
            "timestamp_start": float,
            "timestamp_end": float,
            "duration_seconds": float,
            "text_preview": str,
            "is_speaker_change": bool
        },
        ...
    ],
    "roles": {
        "speaker_id_1": "facilitator",
        "speaker_id_2": "contributor",
        ...
    },
    "summary": {
        "conversation_id": str,
        "conversation_name": str,
        "total_duration": float,
        "total_turns": int,
        "total_speakers": int,
        "started_at": str,  # ISO 8601
        "ended_at": str     # ISO 8601
    }
}
```

---

### Analytics Calculations

#### 1. Time Spoken Calculation

```python
def calculate_time_spoken(self, utterances: List[Utterance]) -> Dict[str, float]
```

**Algorithm:**
1. For each utterance, calculate duration:
   - If `duration_seconds` exists: use it directly
   - Else if `timestamp_start` and `timestamp_end` exist: calculate difference
   - Else: estimate from word count (150 words/minute)
2. Sum durations by speaker_id
3. Return dictionary of speaker_id → total seconds

**Example:**
```python
{
    "alice": 245.5,    # Alice spoke for 245.5 seconds
    "bob": 312.8,      # Bob spoke for 312.8 seconds
    "carol": 89.2      # Carol spoke for 89.2 seconds
}
```

---

#### 2. Turn Distribution Calculation

```python
def calculate_turn_distribution(self, utterances: List[Utterance]) -> Dict[str, int]
```

**Algorithm:**
1. Count utterances per speaker_id using Counter
2. Return dictionary of speaker_id → turn count

**Example:**
```python
{
    "alice": 45,    # Alice had 45 turns
    "bob": 52,      # Bob had 52 turns
    "carol": 18     # Carol had 18 turns
}
```

---

#### 3. Topic Dominance Calculation

```python
def calculate_topic_dominance(self, nodes: List[Node], utterances: List[Utterance]) -> Dict[str, List[str]]
```

**Algorithm:**
1. For each node (topic):
   - Count utterances per speaker within that node
   - Calculate percentage of utterances for each speaker
   - If speaker has >40% of utterances, they "dominate" that topic
2. Return dictionary of speaker_id → list of dominated topic names

**Dominance Threshold:** 40% (configurable)

**Example:**
```python
{
    "alice": ["Project Planning", "Budget Review"],
    "bob": ["Technical Implementation", "Testing Strategy", "Deployment"],
    "carol": []  # Carol didn't dominate any topics
}
```

---

#### 4. Role Detection

```python
def detect_speaker_roles(
    self,
    utterances: List[Utterance],
    nodes: List[Node],
    time_spoken: Dict[str, float],
    turn_distribution: Dict[str, int]
) -> Dict[str, str]
```

**Classification Heuristics:**

| Role | Criteria |
|------|----------|
| **Facilitator** | >30% of turns AND avg turn duration < 10 seconds |
| **Contributor** | >25% of total time spoken AND avg turn duration > 15 seconds |
| **Observer** | <10% of turns |
| **Contributor** (default) | All others |

**Example:**
```python
{
    "alice": "facilitator",  # Many short questions/prompts
    "bob": "contributor",    # Long detailed explanations
    "carol": "observer"      # Few brief comments
}
```

**Role Descriptions:**
- **Facilitator**: Speaks frequently but briefly, distributed across topics. Likely guiding the conversation with questions and prompts.
- **Contributor**: Speaks extensively with longer turns, often dominating specific topics. Primary content provider.
- **Observer**: Speaks infrequently with brief turns. Participates minimally in the conversation.

---

#### 5. Speaker Timeline

```python
def calculate_speaker_timeline(self, utterances: List[Utterance]) -> List[Dict[str, Any]]
```

**Algorithm:**
1. Sort utterances by sequence_number
2. For each utterance:
   - Extract speaker info, timestamps, duration
   - Create text preview (first 100 characters)
   - Detect speaker changes (when speaker differs from previous)
3. Return chronological list of timeline segments

**Example:**
```python
[
    {
        "sequence_number": 1,
        "speaker_id": "alice",
        "speaker_name": "Alice",
        "timestamp_start": 0.0,
        "timestamp_end": 5.2,
        "duration_seconds": 5.2,
        "text_preview": "Let's start by discussing the project goals...",
        "is_speaker_change": True  # First utterance
    },
    {
        "sequence_number": 2,
        "speaker_id": "bob",
        "speaker_name": "Bob",
        "timestamp_start": 5.2,
        "timestamp_end": 18.7,
        "duration_seconds": 13.5,
        "text_preview": "I think we should focus on three main areas: performance, scalability, and...",
        "is_speaker_change": True  # Speaker changed from Alice to Bob
    },
    ...
]
```

---

## API Endpoints

### 1. Get Full Analytics

```http
GET /api/analytics/conversations/{conversation_id}/analytics
```

**Response:** Complete analytics object (see "Main Method" section above)

**Status Codes:**
- `200 OK`: Analytics calculated successfully
- `404 Not Found`: No data found for conversation
- `500 Internal Server Error`: Calculation failed

**Example:**
```bash
curl http://localhost:8000/api/analytics/conversations/123e4567-e89b-12d3-a456-426614174000/analytics
```

---

### 2. Get Speaker Stats

```http
GET /api/analytics/conversations/{conversation_id}/speakers/{speaker_id}
```

**Response:**
```json
{
    "speaker_id": "alice",
    "speaker_name": "Alice",
    "time_spoken_seconds": 245.5,
    "time_spoken_percentage": 37.9,
    "turn_count": 45,
    "turn_percentage": 39.1,
    "topics_dominated": ["Project Planning", "Budget Review"],
    "role": "facilitator",
    "avg_turn_duration": 5.4
}
```

**Status Codes:**
- `200 OK`: Speaker found
- `404 Not Found`: Speaker not found in conversation
- `500 Internal Server Error`: Failed to get stats

---

### 3. Get Timeline

```http
GET /api/analytics/conversations/{conversation_id}/timeline
```

**Response:** Array of timeline segments (see "Speaker Timeline" section)

**Status Codes:**
- `200 OK`: Timeline retrieved
- `500 Internal Server Error`: Failed to get timeline

---

### 4. Get Roles

```http
GET /api/analytics/conversations/{conversation_id}/roles
```

**Response:**
```json
{
    "alice": "facilitator",
    "bob": "contributor",
    "carol": "observer"
}
```

**Status Codes:**
- `200 OK`: Roles retrieved
- `500 Internal Server Error`: Failed to get roles

---

## Frontend Implementation

### Analytics Page Component

Located at `src/pages/Analytics.jsx`, this page displays all speaker analytics.

#### Features

1. **Summary Cards**: Total duration, turns, speakers, avg turn duration
2. **Speaker Cards**: Individual speaker statistics with:
   - Time spoken (percentage bar + total time)
   - Turn count (percentage bar + total count)
   - Average turn duration
   - Role badge with icon
   - Dominated topics (up to 3 shown, expandable)
3. **Sorting**: Sort speakers by time, turns, or topics dominated
4. **Selection**: Click speaker card to see detailed view
5. **Timeline Visualization**: Chronological bar chart of speaker activity

#### Navigation

**Access:** `/analytics/{conversationId}`

**From Conversation View:**
```jsx
<Link to={`/analytics/${conversationId}`}>View Analytics</Link>
```

---

### Analytics API Client

Located at `src/services/analyticsApi.js`, provides functions to call backend endpoints.

#### Functions

```javascript
// Fetch complete analytics
const analytics = await fetchConversationAnalytics(conversationId);

// Fetch specific speaker stats
const speaker = await fetchSpeakerStats(conversationId, speakerId);

// Fetch timeline only
const timeline = await fetchSpeakerTimeline(conversationId);

// Fetch roles only
const roles = await fetchSpeakerRoles(conversationId);
```

---

## UI/UX Design

### Color Scheme

**Role Colors:**
- **Facilitator**: Blue (`bg-blue-100`, `text-blue-800`, `border-blue-300`)
- **Contributor**: Green (`bg-green-100`, `text-green-800`, `border-green-300`)
- **Observer**: Gray (`bg-gray-100`, `text-gray-800`, `border-gray-300`)

**Role Icons:**
- **Facilitator**: 🎯 (target - directing conversation)
- **Contributor**: 💬 (speech bubble - providing content)
- **Observer**: 👁️ (eye - watching/listening)

---

### Speaker Card Layout

```
┌─────────────────────────────────────────┐
│ Speaker Name                   🎯 Role  │
│                                          │
│ Time Spoken              37.9%          │
│ ████████████░░░░░░░░░                   │
│ 4m 5s                                   │
│                                          │
│ Turns                    39.1%          │
│ ████████████░░░░░░░░░                   │
│ 45 turns                                │
│                                          │
│ Avg Turn: 5.4s                          │
│                                          │
│ ───────────────────────────────────     │
│ Dominated Topics (2)                    │
│ [Project Planning] [Budget Review]      │
└─────────────────────────────────────────┘
```

---

### Timeline Visualization

```
Speaker Timeline
┌─────────────────────────────────────────┐
│ ● Alice  ██████ "Let's start by..."  0s │
│   Bob    ████████████ "I think we..."5s │
│ ● Alice  ████ "That sounds..."      18s │
│   Alice  █████ "What about..."      23s │
│ ● Carol  ███ "I agree with..."      28s │
│ ● Bob    ███████████ "The technical..."│
└─────────────────────────────────────────┘

● = Speaker change
Bar width = Duration
Color = Role (blue/green/gray)
```

---

## Performance Considerations

### Optimization Strategies

1. **Caching**: Analytics results cached in-memory for 5 minutes
2. **Batch Queries**: Fetch all utterances and nodes in single query
3. **Lazy Loading**: Timeline only loaded when tab opened
4. **Indexing**: Database indexes on `conversation_id` and `speaker_id`

### Scalability

**Tested Limits:**
- Conversations: Up to 2 hours (3000+ utterances)
- Speakers: Up to 20 participants
- Calculation Time: < 2 seconds for 1-hour conversation

**Future Optimizations:**
- Pre-calculate analytics on graph generation
- Store analytics in database (cached)
- Background job for large conversations (>5000 utterances)

---

## Testing

### Backend Tests

```python
# tests/test_speaker_analytics.py

def test_calculate_time_spoken():
    """Test time calculation from utterances"""
    # Test with explicit duration_seconds
    # Test with timestamp_start/end
    # Test with estimated duration (word count)

def test_calculate_turn_distribution():
    """Test turn counting per speaker"""
    # Test with equal distribution
    # Test with skewed distribution

def test_detect_facilitator_role():
    """Test facilitator detection (many short turns)"""
    # Speaker with >30% turns, avg <10s → facilitator

def test_detect_contributor_role():
    """Test contributor detection (long turns, high time)"""
    # Speaker with >25% time, avg >15s → contributor

def test_detect_observer_role():
    """Test observer detection (few turns)"""
    # Speaker with <10% turns → observer

def test_topic_dominance():
    """Test topic dominance calculation"""
    # Speaker with >40% utterances in node → dominates topic
    # Speaker with <40% → doesn't dominate

def test_timeline_speaker_changes():
    """Test speaker change detection"""
    # First utterance should have is_speaker_change=True
    # Consecutive same speaker should have is_speaker_change=False
    # Speaker switch should have is_speaker_change=True
```

### Frontend Tests

```javascript
// Analytics.test.jsx

describe('Analytics Page', () => {
  it('displays summary cards with correct stats')
  it('renders speaker cards sorted by time')
  it('allows re-sorting by turns and topics')
  it('expands speaker details on click')
  it('displays timeline visualization')
  it('handles loading state')
  it('handles error state with retry button')
})

// analyticsApi.test.js

describe('Analytics API Client', () => {
  it('fetches full analytics successfully')
  it('fetches specific speaker stats')
  it('handles 404 errors gracefully')
  it('handles network errors')
})
```

---

## Usage Examples

### Example 1: Meeting Analysis

**Scenario:** 1-hour team standup with 5 participants

**Analytics Results:**
```json
{
    "speakers": {
        "scrum_master": {
            "speaker_name": "Sarah (Scrum Master)",
            "role": "facilitator",
            "time_spoken_percentage": 15.2,
            "turn_count": 45,
            "topics_dominated": []
        },
        "tech_lead": {
            "speaker_name": "Bob (Tech Lead)",
            "role": "contributor",
            "time_spoken_percentage": 32.8,
            "turn_count": 28,
            "topics_dominated": ["Technical Challenges", "Architecture Discussion"]
        },
        "dev1": {
            "speaker_name": "Alice (Developer)",
            "role": "contributor",
            "time_spoken_percentage": 21.5,
            "turn_count": 22,
            "topics_dominated": ["Feature Implementation"]
        },
        "dev2": {
            "speaker_name": "Charlie (Developer)",
            "role": "contributor",
            "time_spoken_percentage": 18.9,
            "turn_count": 19,
            "topics_dominated": ["Testing Strategy"]
        },
        "designer": {
            "speaker_name": "Diana (Designer)",
            "role": "observer",
            "time_spoken_percentage": 11.6,
            "turn_count": 8,
            "topics_dominated": []
        }
    },
    "summary": {
        "total_duration": 3720,  // 62 minutes
        "total_turns": 122,
        "total_speakers": 5
    }
}
```

**Insights:**
- Sarah effectively facilitates (many short prompts, 45 turns)
- Bob is primary technical contributor (32.8% speaking time, 2 topics dominated)
- Diana is relatively quiet (11.6%, only 8 turns) - may need encouragement to participate

---

### Example 2: Interview Analysis

**Scenario:** 45-minute job interview

**Analytics Results:**
```json
{
    "speakers": {
        "interviewer": {
            "role": "facilitator",
            "time_spoken_percentage": 38.5,
            "turn_count": 52,
            "avg_turn_duration": 8.3
        },
        "candidate": {
            "role": "contributor",
            "time_spoken_percentage": 61.5,
            "turn_count": 48,
            "avg_turn_duration": 14.7
        }
    }
}
```

**Insights:**
- Candidate spoke more (61.5% vs 38.5%) - good engagement
- Interviewer had more turns (52 vs 48) - asking questions effectively
- Candidate's avg turn (14.7s) > interviewer's (8.3s) - detailed responses

---

## Future Enhancements

### Phase 1 (Week 9-10)
- [ ] Export analytics to CSV/PDF
- [ ] Compare multiple conversations
- [ ] Filter timeline by speaker
- [ ] Sentiment analysis per speaker

### Phase 2 (Week 11-12)
- [ ] Speaking style analysis (pace, pauses, interruptions)
- [ ] Network graph of speaker interactions
- [ ] Topic transition analysis (who drives topic changes)
- [ ] Speaking balance recommendations

### Phase 3 (Week 13-14)
- [ ] Real-time analytics during live conversations
- [ ] ML-based role prediction improvements
- [ ] Custom role definitions
- [ ] Analytics dashboard widgets

---

## Troubleshooting

### Issue: Analytics show 0 seconds for all speakers

**Cause:** Utterances missing `duration_seconds`, `timestamp_start`/`end` fields

**Solution:**
1. Check Google Meet parser is calculating timestamps correctly
2. Verify database migration included timestamp fields
3. Re-import transcript if data is missing

**Verify:**
```sql
SELECT id, speaker_id, duration_seconds, timestamp_start, timestamp_end
FROM utterances
WHERE conversation_id = 'your-conversation-id'
LIMIT 10;
```

---

### Issue: All speakers classified as "contributor"

**Cause:** Role detection heuristics not matching any specific criteria

**Solution:**
1. Check that `time_spoken` and `turn_distribution` are calculated correctly
2. Verify thresholds (30%, 25%, 10%) are appropriate for your conversation
3. Adjust heuristics in `detect_speaker_roles()` if needed

**Debug:**
```python
# Log intermediate values
print(f"Time %: {time_percentage}")
print(f"Turn %: {turn_percentage}")
print(f"Avg duration: {avg_turn_duration}")
```

---

### Issue: Topic dominance shows empty lists for all speakers

**Cause:** Nodes missing `utterance_ids` or mismatched IDs

**Solution:**
1. Verify graph generation populates `utterance_ids` for each node
2. Check that utterance IDs are UUIDs, not integers
3. Re-generate graph if data is missing

**Verify:**
```sql
SELECT id, node_name, utterance_ids
FROM nodes
WHERE conversation_id = 'your-conversation-id'
LIMIT 10;
```

---

### Issue: Frontend shows "No analytics data found"

**Cause:** Backend returning empty `speakers` object

**Solution:**
1. Check conversation has utterances: `GET /api/conversations/{id}`
2. Verify utterances have speaker_id populated
3. Check backend logs for errors during calculation

**Debug:**
```bash
# Check backend logs
tail -f /var/log/lct-backend.log | grep "analytics"

# Test endpoint directly
curl http://localhost:8000/api/analytics/conversations/{id}/analytics
```

---

## Related Documentation

- [GRAPH_GENERATION.md](./GRAPH_GENERATION.md) - Week 4 graph generation (source of nodes)
- [GOOGLE_MEET_IMPORT.md](./GOOGLE_MEET_IMPORT.md) - Week 3 transcript parsing (source of utterances)
- [DATA_MODEL_V2.md](../docs/DATA_MODEL_V2.md) - Database schema for utterances and nodes
- [ROADMAP.md](../docs/ROADMAP.md) - Overall project roadmap

---

## Summary

Week 8 introduces comprehensive speaker analytics including:

1. **Quantitative Metrics**: Time spoken, turn count, average turn duration
2. **Qualitative Analysis**: Role detection (facilitator/contributor/observer)
3. **Topic Analysis**: Which speakers dominated which topics
4. **Visualization**: Timeline showing speaker activity chronologically
5. **Comparison**: Side-by-side speaker statistics

**Key Benefits:**
- Understand conversation dynamics and participation patterns
- Identify dominant speakers and topics
- Detect facilitation effectiveness
- Analyze engagement levels
- Export data for reporting

This completes Week 8 of the Live Conversational Threads V2 roadmap.
