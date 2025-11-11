# Live Conversational Threads - Implementation Roadmap

**Version:** 2.0
**Last Updated:** 2025-11-11
**Status:** Planning Phase

## Executive Summary

This roadmap outlines the 14-week implementation plan for transforming Live Conversational Threads into a comprehensive conversation analysis platform with Google Meet transcript support, multi-scale graph visualization, and advanced analytical features.

**Key Milestones:**
- Weeks 1-4: Foundation (data model, instrumentation, Google Meet import)
- Weeks 5-7: Core Features (dual-view, zoom levels, node detail)
- Weeks 8-10: Analysis Features (speaker analytics, prompts config)
- Weeks 11-14: Advanced Features (Simulacra levels, cognitive bias detection)

**Risk Level:** Medium
**Dependencies:** PostgreSQL, FastAPI, React, OpenAI API
**Estimated Total Cost:** $500-1000 (LLM API usage for testing/development)

---

## Phase 1: Foundation & Infrastructure (Weeks 1-4)

### Week 1: Database Schema Migration

**Goal:** Implement DATA_MODEL_V2.md schema with full instrumentation support

**Tasks:**
1. Create Alembic migration scripts for new tables:
   - `utterances` (speaker diarization support)
   - `nodes` (enhanced with zoom_level_visible)
   - `edges` (temporal vs contextual relationships)
   - `clusters` (hierarchical grouping)
   - `edits_log` (training data collection)
   - `api_calls_log` (cost tracking)

2. Write database initialization scripts
3. Create test fixtures for all tables
4. Implement rollback procedures

**Success Criteria:**
- All migrations run cleanly on fresh PostgreSQL instance
- Sample data populates correctly
- Rollback tested and verified

**Testing:**
```bash
# Unit tests for schema
pytest tests/test_database_schema.py -v

# Migration tests
pytest tests/test_migrations.py -v
```

**Metrics:**
- Migration execution time: < 5 seconds
- Test coverage: 100% for database models

---

### Week 2: Instrumentation & Cost Tracking

**Goal:** Implement comprehensive API call logging and cost monitoring

**Tasks:**
1. Create `track_api_call` decorator (see TIER_2_FEATURES.md)
2. Implement cost calculation functions for:
   - OpenAI models (GPT-4, GPT-3.5-turbo)
   - Anthropic models (Claude Sonnet-4)
   - Token counting utilities
3. Build background job for cost aggregation
4. Create alert system for cost thresholds

**Code Structure:**
```
lct_python_backend/
├── instrumentation/
│   ├── __init__.py
│   ├── decorators.py       # @track_api_call
│   ├── cost_calculator.py  # Token cost logic
│   ├── alerts.py           # Cost threshold alerts
│   └── aggregation.py      # Daily/weekly rollups
```

**Success Criteria:**
- Every LLM API call logged to `api_calls_log`
- Cost calculated within 1% accuracy
- Dashboard shows real-time cost tracking

**Testing:**
```python
# tests/test_instrumentation.py
def test_track_api_call_decorator():
    """Test that API calls are logged with correct cost"""

def test_cost_calculation_gpt4():
    """Test GPT-4 cost calculation for various token counts"""

def test_cost_alert_threshold():
    """Test alert triggers when cost exceeds threshold"""
```

**Metrics to Track:**
- API call latency (p50, p95, p99)
- Token usage per endpoint
- Cost per conversation
- Cost per feature (clustering, bias detection, etc.)
- Model selection distribution

**Storage Plan:**
- Retain raw logs: 90 days
- Retain aggregated metrics: 2 years
- Archive strategy: Export to CSV monthly

---

### Week 3: Google Meet Transcript Parser

**Goal:** Robust parser for Google Meet PDF/TXT transcripts with speaker diarization

**Tasks:**
1. Implement PDF extraction using PyPDF2/pdfplumber
2. Parse transcript format: `Speaker Name ~: utterance text`
3. Extract timestamps (e.g., `00:10:47` section markers)
4. Handle edge cases:
   - Speakers without `~` suffix
   - Multi-line utterances
   - Special characters in names
   - Missing timestamps

5. Create data validation layer
6. Build import API endpoint: `POST /import/google-meet`

**Code Structure:**
```python
# lct_python_backend/parsers/google_meet.py

class GoogleMeetParser:
    def parse_pdf(self, file_path: str) -> ParsedTranscript:
        """Extract text from PDF and parse structure"""

    def parse_speakers(self, text: str) -> List[Utterance]:
        """Identify speakers and utterances"""

    def calculate_timestamps(self, utterances: List[Utterance]) -> List[Utterance]:
        """Calculate start/end times for each utterance"""

    def validate_transcript(self, transcript: ParsedTranscript) -> ValidationResult:
        """Check for parsing errors and ambiguities"""
```

**Success Criteria:**
- Parse 100% of test transcripts without errors
- Correctly identify 95%+ of speaker boundaries
- Handle malformed input gracefully

**Testing:**
```python
# tests/test_google_meet_parser.py
def test_parse_simple_transcript():
    """Test basic speaker diarization"""

def test_parse_multiline_utterance():
    """Test utterances spanning multiple lines"""

def test_parse_missing_timestamps():
    """Test handling of incomplete timestamp data"""

def test_parse_special_characters():
    """Test names with unicode, punctuation"""
```

**Test Data:**
- 10 real Google Meet transcripts (anonymized)
- 5 synthetic edge case transcripts
- 3 malformed transcripts (error handling)

**Metrics:**
- Parse success rate: > 95%
- Parse time: < 2 seconds per 10k words
- Speaker detection accuracy: > 90%

---

### Week 4: Initial Graph Generation

**Goal:** Baseline AI-powered graph generation from parsed transcripts

**Tasks:**
1. Implement prompt-based clustering (see ADR-002)
2. Create initial node generation endpoint
3. Build temporal edge creation logic
4. Implement basic contextual relationships

**Prompts to Implement:**
```json
{
  "initial_clustering": {
    "description": "Generate initial topic-based nodes from transcript",
    "template": "Analyze this transcript and identify natural topic shifts...",
    "model": "gpt-4",
    "temperature": 0.5
  }
}
```

**Success Criteria:**
- Generate graph from transcript in < 30 seconds
- Node granularity appropriate for 5 zoom levels
- Temporal edges connect all nodes sequentially

**Testing:**
```python
def test_initial_clustering():
    """Test that transcript generates reasonable node structure"""

def test_zoom_level_distribution():
    """Test that nodes span all 5 zoom levels appropriately"""
```

**Metrics:**
- Token cost per conversation: < $2.00
- Graph generation latency: < 60 seconds
- User satisfaction: Manual review of 10 test graphs

---

## Phase 2: Core Features (Weeks 5-7)

### Week 5: Dual-View Architecture

**Goal:** Implement Timeline (bottom) + Contextual Network (top) UI

**Tasks:**
1. Split canvas into 15% (timeline) + 85% (network)
2. Implement synchronized zoom/pan
3. Create temporal ordering visualization
4. Build contextual clustering layout

**React Components:**
```typescript
// src/components/DualView/
├── DualViewCanvas.tsx        // Main container
├── TimelineView.tsx          // Bottom 15%
├── ContextualNetworkView.tsx // Top 85%
└── SyncController.tsx        // Zoom/pan sync
```

**Success Criteria:**
- Both views visible simultaneously
- Zoom/pan synchronized perfectly
- Performance: 60 FPS with 100+ nodes

**Testing:**
```typescript
// tests/DualViewCanvas.test.tsx
describe('DualViewCanvas', () => {
  it('renders both views with correct proportions')
  it('synchronizes zoom across views')
  it('maintains performance with large graphs')
})
```

**Metrics:**
- Render time: < 100ms
- Frame rate: 60 FPS
- Memory usage: < 200MB for 500 nodes

---

### Week 6: 5-Level Zoom System

**Goal:** Implement discrete zoom levels: sentence → turn → topic → theme → arc

**Tasks:**
1. Implement `ZoomController` with 5 quantized levels
2. Create visibility logic for nodes based on `zoom_level_visible`
3. Build smooth transitions between levels
4. Implement zoom-dependent context loading

**Zoom Level Definitions:**
```typescript
enum ZoomLevel {
  SENTENCE = 1,    // Individual sentences (zoom > 0.8)
  TURN = 2,        // Speaker turns (0.6 < zoom ≤ 0.8)
  TOPIC = 3,       // Topic segments (0.4 < zoom ≤ 0.6)
  THEME = 4,       // Thematic clusters (0.2 < zoom ≤ 0.4)
  ARC = 5          // Narrative arcs (zoom ≤ 0.2)
}
```

**Success Criteria:**
- Zoom transitions smooth and intuitive
- Node visibility updates correctly at each level
- No performance degradation during zoom

**Testing:**
```typescript
describe('ZoomController', () => {
  it('quantizes zoom values to 5 discrete levels')
  it('shows/hides nodes based on zoom_level_visible')
  it('loads appropriate context for each level')
})
```

**Metrics:**
- Zoom transition latency: < 50ms
- Node culling efficiency: Only visible nodes rendered
- User experience: A/B test with 10 users

---

### Week 7: Node Detail Panel

**Goal:** Split-screen detail view with zoom-dependent context

**Tasks:**
1. Implement panel that shows selected node
2. Build context loading logic (see TIER_2_FEATURES.md Section 1)
3. Create inline editing interface
4. Implement edit mode toggle

**Context Loading Rules:**
```typescript
function getContextConfig(zoom: ZoomLevel): ContextConfig {
  switch(zoom) {
    case ZoomLevel.SENTENCE:
      return { previous: 2, next: 2, mode: 'detailed' }
    case ZoomLevel.TURN:
      return { previous: 1, next: 1, mode: 'focused' }
    case ZoomLevel.ARC:
      return { mode: 'summary', summary_of: 'entire_thread' }
  }
}
```

**Success Criteria:**
- Context loads within 200ms
- Edit mode requires explicit toggle (intentional friction)
- Changes save immediately to backend

**Testing:**
```typescript
describe('NodeDetailPanel', () => {
  it('loads correct context based on zoom level')
  it('requires edit mode toggle for changes')
  it('saves edits to backend immediately')
})
```

**Metrics:**
- Context load time: < 200ms
- Edit save latency: < 100ms
- Edit mode activation rate: Track user behavior

---

## Phase 3: Analysis Features (Weeks 8-10)

### Week 8: Speaker Analytics

**Goal:** Comprehensive speaker statistics and role detection

**Tasks:**
1. Implement analytics calculations:
   - Time spoken per speaker
   - Turn count and distribution
   - Topics dominated by each speaker
   - Role detection (facilitator, contributor, observer)

2. Build analytics API endpoint: `GET /conversations/{id}/analytics`
3. Create Analytics UI page (separate from main graph)
4. Implement speaker timeline visualization

**Analytics Calculations:**
```python
# lct_python_backend/analytics/speaker_analytics.py

class SpeakerAnalytics:
    def calculate_time_spoken(self, conversation_id: str) -> Dict[str, float]:
        """Calculate seconds spoken per speaker"""

    def calculate_turn_distribution(self, conversation_id: str) -> Dict[str, int]:
        """Count turns per speaker"""

    def detect_speaker_roles(self, conversation_id: str) -> Dict[str, str]:
        """Classify speakers: facilitator, contributor, observer, etc."""

    def calculate_topic_dominance(self, conversation_id: str) -> Dict[str, List[str]]:
        """Identify which topics each speaker dominated"""
```

**Success Criteria:**
- Analytics calculated for any conversation
- Role detection > 70% accuracy (manual validation)
- UI loads analytics in < 1 second

**Testing:**
```python
def test_speaker_time_calculation():
    """Test time spoken calculated correctly from timestamps"""

def test_role_detection():
    """Test role classifier on labeled dataset"""

def test_analytics_performance():
    """Test analytics generation scales to 2-hour conversations"""
```

**Metrics:**
- Analytics generation time: < 5 seconds
- Accuracy of role detection: > 70%
- User engagement: Track analytics view count

---

### Week 9: Prompts Configuration System

**Goal:** User-editable JSON prompts with UI settings panel

**Tasks:**
1. Create `prompts.json` configuration file
2. Implement prompt template rendering with variables
3. Build Settings UI for prompt editing
4. Create prompt versioning system
5. Implement hot-reload for prompt changes

**Prompts Configuration Schema:**
```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-11",
  "prompts": {
    "initial_clustering": {
      "description": "Generate initial nodes from transcript",
      "template": "...",
      "model": "gpt-4",
      "temperature": 0.5,
      "max_tokens": 2000,
      "few_shot_examples": [...]
    },
    "detect_cognitive_bias": {
      "description": "Identify cognitive biases in utterances",
      "template": "...",
      "model": "gpt-4",
      "temperature": 0.3
    }
  }
}
```

**Success Criteria:**
- All prompts externalized to JSON
- Users can edit prompts via UI
- Prompt changes take effect immediately
- Version history maintained

**Testing:**
```python
def test_prompt_template_rendering():
    """Test variable substitution in prompts"""

def test_prompt_hot_reload():
    """Test prompt updates apply without restart"""

def test_prompt_versioning():
    """Test prompt changes create version history"""
```

**Metrics:**
- Prompt edit frequency: Track user customization
- Prompt performance: A/B test custom vs default
- Token usage: Monitor cost impact of edits

---

### Week 10: Edit History & Training Data Export

**Goal:** Complete logging and export system for AI training data

**Tasks:**
1. Ensure all edits logged to `edits_log` table
2. Implement export endpoint: `GET /conversations/{id}/training-data`
3. Create export formats:
   - JSONL (for fine-tuning)
   - CSV (for analysis)
   - Markdown (for human review)

4. Build diff visualization for edits
5. Implement feedback annotation UI

**Export Format (JSONL):**
```json
{
  "messages": [
    {"role": "system", "content": "You are analyzing conversation transcripts..."},
    {"role": "user", "content": "Original AI output: [node summary]"},
    {"role": "assistant", "content": "User correction: [edited summary]"}
  ],
  "metadata": {
    "conversation_id": "uuid",
    "edit_type": "node_summary_edit",
    "timestamp": "2025-11-11T10:30:00Z",
    "feedback": "User noted AI missed sarcasm in utterance"
  }
}
```

**Success Criteria:**
- 100% of edits captured in `edits_log`
- Export generates valid fine-tuning format
- User can annotate edits with feedback

**Testing:**
```python
def test_edit_logging():
    """Test all edit types logged correctly"""

def test_training_data_export():
    """Test export generates valid JSONL format"""

def test_diff_visualization():
    """Test diff correctly shows before/after"""
```

**Metrics:**
- Edit capture rate: 100%
- Export file size: Track data volume
- User feedback rate: % of edits annotated

---

## Phase 4: Advanced Features (Weeks 11-14)

### Week 11: Simulacra Level Detection (Phase 1)

**Goal:** Implement basic Simulacra level classification for utterances

**Tasks:**
1. Create Simulacra level prompt with heuristics
2. Implement pattern matching for obvious cases
3. Build LLM-based contextual analysis
4. Create UI indicators for detected levels

**Implementation Approach:**
```python
# lct_python_backend/analysis/simulacra.py

class SimulacraDetector:
    def classify_utterance(self, utterance: Utterance, context: List[Utterance]) -> SimulacraLevel:
        """
        Classify utterance as Level 1, 2, 3, or 4
        Using heuristics + LLM analysis
        """

    def detect_level_1_patterns(self, text: str) -> bool:
        """Pattern match for object-level claims"""

    def detect_level_2_manipulation(self, utterance: Utterance, context: List[Utterance]) -> bool:
        """Detect persuasion/manipulation patterns"""

    def detect_level_3_signaling(self, utterance: Utterance, speaker: str) -> bool:
        """Detect tribal/group signaling"""
```

**Success Criteria:**
- Detect obvious Level 1 (facts) and Level 3 (signaling)
- LLM analysis for ambiguous cases
- UI shows level indicators on utterances

**Testing:**
```python
def test_level_1_detection():
    """Test detection of factual, object-level statements"""

def test_level_3_signaling():
    """Test detection of tribal signaling"""

def test_ambiguous_classification():
    """Test LLM handles edge cases"""
```

**Metrics:**
- Classification accuracy: Manual validation on 100 utterances
- False positive rate: < 20%
- Token cost per conversation: < $1.50

---

### Week 12: Cognitive Bias Detection (Phase 1)

**Goal:** Implement detection for top 10 most common cognitive biases

**Priority Biases:**
1. Confirmation bias
2. Affect heuristic
3. Optimism bias
4. Straw man fallacy
5. Ad hominem
6. Whataboutism
7. False dichotomy
8. Appeal to nature
9. Sunk cost fallacy
10. Availability heuristic

**Implementation:**
```python
# lct_python_backend/analysis/cognitive_bias.py

class CognitiveBiasDetector:
    def detect_confirmation_bias(self, utterances: List[Utterance]) -> List[BiasInstance]:
        """Detect selective evidence presentation"""

    def detect_straw_man(self, utterances: List[Utterance]) -> List[BiasInstance]:
        """Detect misrepresentation of opponent's position"""

    def detect_whataboutism(self, utterances: List[Utterance]) -> List[BiasInstance]:
        """Pattern match + contextual analysis for whataboutism"""
```

**Detection Pipeline:**
1. Fast pattern matching (regex, keyword spotting)
2. Contextual LLM analysis for confirmed candidates
3. Confidence scoring (0.0 - 1.0)
4. UI annotation with explanations

**Success Criteria:**
- Detect 70%+ of biases in test dataset
- False positive rate < 30%
- Clear explanations for each detection

**Testing:**
```python
def test_confirmation_bias_detection():
    """Test detection on labeled examples"""

def test_straw_man_detection():
    """Test pattern matching + LLM analysis"""

def test_confidence_scoring():
    """Test confidence scores correlate with accuracy"""
```

**Metrics:**
- Detection accuracy per bias type
- Token cost per conversation
- User feedback on false positives

---

### Week 13: Implicit Frame Detection

**Goal:** Identify hidden worldviews and normative assumptions in conversations

**Tasks:**
1. Implement frame extraction prompts
2. Detect "is-ought" conflations
3. Identify hidden premises
4. Build frame taxonomy UI

**Frame Detection Approach:**
```python
class ImplicitFrameDetector:
    def extract_normative_claims(self, utterances: List[Utterance]) -> List[NormativeClaim]:
        """Identify statements about what 'should' be"""

    def detect_hidden_premises(self, claim: NormativeClaim) -> List[Premise]:
        """Unpack unstated assumptions"""

    def detect_is_ought_conflation(self, utterances: List[Utterance]) -> List[Conflation]:
        """Find naturalistic fallacy instances"""
```

**Example Output:**
```json
{
  "normative_claim": "We should prioritize economic growth",
  "hidden_premises": [
    "Economic growth increases human wellbeing",
    "Economic growth is sustainable",
    "Current distribution mechanisms are fair"
  ],
  "conflations": [
    {
      "type": "is_ought",
      "text": "Humans naturally seek wealth, so capitalism is right",
      "explanation": "Conflates descriptive claim (humans seek wealth) with normative claim (capitalism is right)"
    }
  ]
}
```

**Success Criteria:**
- Extract meaningful frames from 60%+ of conversations
- Clear, understandable explanations
- UI shows frame taxonomy tree

**Testing:**
```python
def test_normative_claim_extraction():
    """Test extraction of 'should' statements"""

def test_hidden_premise_detection():
    """Test unpacking of unstated assumptions"""

def test_is_ought_detection():
    """Test naturalistic fallacy detection"""
```

**Metrics:**
- Frame extraction rate: % of conversations with frames
- User agreement with detected frames: Manual validation
- Token cost per conversation

---

### Week 14: Integration, Polish & Deployment

**Goal:** End-to-end testing, performance optimization, documentation

**Tasks:**
1. End-to-end integration tests for all features
2. Performance profiling and optimization
3. User acceptance testing (10 beta testers)
4. Documentation updates
5. Deployment to production environment
6. Monitoring and alerting setup

**Integration Tests:**
```python
def test_full_pipeline_google_meet_to_analysis():
    """
    Test complete flow:
    1. Import Google Meet transcript
    2. Generate graph with 5 zoom levels
    3. Run speaker analytics
    4. Detect Simulacra levels
    5. Detect cognitive biases
    6. Export training data
    """

def test_cost_tracking_end_to_end():
    """Test all API calls logged and costs calculated"""

def test_edit_history_round_trip():
    """Test edit → log → export → import for training"""
```

**Performance Optimization Targets:**
- Initial graph load: < 2 seconds
- Zoom transition: < 50ms
- Analytics calculation: < 5 seconds
- Bias detection: < 30 seconds

**Documentation to Update:**
- User guide (how to import transcripts, use features)
- API documentation (all endpoints, schemas)
- Developer setup guide
- Architecture diagrams
- Prompt engineering guide

**Deployment Checklist:**
- [ ] Database migration scripts tested on staging
- [ ] Environment variables configured
- [ ] API keys secured in secrets manager
- [ ] Monitoring dashboard configured
- [ ] Alert thresholds set for costs and errors
- [ ] Backup strategy implemented
- [ ] Rollback plan documented

**Metrics:**
- All tests passing (100% critical path)
- Performance targets met
- User satisfaction: Survey beta testers
- Zero P0 bugs in production

---

## Storage Plan

### Database Strategy

**PostgreSQL Configuration:**
```yaml
database:
  host: localhost
  port: 5432
  name: lct_production
  max_connections: 100
  connection_timeout: 30s
```

**Table Size Estimates (for 1000 conversations):**
- `conversations`: ~100 KB
- `utterances`: ~500 MB (avg 1000 utterances/conversation)
- `nodes`: ~50 MB (avg 50 nodes/conversation)
- `edges`: ~30 MB (avg 100 edges/conversation)
- `clusters`: ~10 MB
- `edits_log`: ~20 MB (assuming 10% edit rate)
- `api_calls_log`: ~100 MB (detailed logs)

**Total Storage:** ~710 MB for 1000 conversations

**Retention Policy:**
- Conversation data: Indefinite (user-managed deletion)
- Raw API logs: 90 days
- Aggregated metrics: 2 years
- Edit history: Indefinite (training data)

**Backup Strategy:**
- Full backup: Daily at 2 AM
- Incremental backup: Every 6 hours
- Point-in-time recovery: 30 days
- Offsite replication: Google Cloud Storage
- Backup retention: 90 days

**Scaling Plan:**
- Vertical scaling: Increase PostgreSQL instance size
- Horizontal scaling: Read replicas for analytics queries
- Partitioning: Partition `api_calls_log` by month
- Archiving: Move old conversations to cold storage (S3)

### File Storage

**Google Cloud Storage Buckets:**
```
lct-conversations/
  ├── transcripts/        # Original uploaded files
  ├── exports/            # Training data exports
  └── backups/            # Database backups

Structure:
  transcripts/{conversation_id}/{filename}
  exports/{conversation_id}/training-data-{timestamp}.jsonl
  backups/postgres-{date}.sql.gz
```

**Storage Costs (Estimate):**
- 1000 conversations × 100 KB transcript = 100 MB
- GCS Standard Storage: $0.02/GB/month
- **Monthly Cost:** ~$0.01 (negligible)

---

## Instrumentation Plan

### Metrics to Track

**Application Metrics:**
```python
# Cost Metrics
- cost_per_conversation_usd
- cost_per_feature_usd (clustering, bias_detection, etc.)
- cost_by_model (gpt4, gpt3.5, claude)
- total_daily_cost_usd
- cost_per_user

# Performance Metrics
- api_call_latency_ms (p50, p95, p99)
- graph_generation_time_seconds
- zoom_transition_time_ms
- analytics_calculation_time_seconds
- frontend_render_time_ms

# Usage Metrics
- conversations_created_total
- transcripts_imported_total
- nodes_created_total (by_ai, by_user)
- edits_made_total (by_type)
- zoom_level_changes_total
- speaker_analytics_views_total
- bias_detections_total (by_type)

# Quality Metrics
- parse_success_rate
- speaker_detection_accuracy
- bias_detection_confidence (avg)
- user_feedback_score (1-5)
- edit_frequency (edits / nodes)

# System Metrics
- database_query_time_ms
- database_connection_pool_usage
- api_request_rate
- error_rate (by_endpoint)
- active_users
```

### Monitoring Stack

**Tools:**
- Prometheus: Metrics collection
- Grafana: Dashboards
- Sentry: Error tracking
- Datadog (alternative): All-in-one monitoring

**Dashboard Layout:**
```
Dashboard 1: Cost Tracking
  - Total daily cost (line chart)
  - Cost by model (pie chart)
  - Cost per conversation (histogram)
  - Cost alerts (threshold indicators)

Dashboard 2: Performance
  - API latency (line chart with p50/p95/p99)
  - Graph generation time (histogram)
  - Database query performance (heat map)
  - Frontend render time (line chart)

Dashboard 3: Usage
  - Conversations created (bar chart)
  - Active users (line chart)
  - Feature usage (stacked area chart)
  - Edit frequency (line chart)

Dashboard 4: Quality
  - Parse success rate (gauge)
  - Bias detection confidence (histogram)
  - User feedback scores (bar chart)
  - Error rate (line chart)
```

**Alerting Rules:**
```yaml
alerts:
  - name: high_daily_cost
    condition: total_daily_cost_usd > 100
    severity: warning
    channel: email, slack

  - name: api_latency_spike
    condition: api_call_latency_p95 > 5000
    severity: critical
    channel: pagerduty

  - name: parse_failure_rate
    condition: parse_success_rate < 0.9
    severity: warning
    channel: slack

  - name: database_connection_exhaustion
    condition: database_connection_pool_usage > 0.8
    severity: critical
    channel: pagerduty
```

### Instrumentation Code

**FastAPI Middleware:**
```python
# lct_python_backend/instrumentation/middleware.py

from prometheus_client import Counter, Histogram, Gauge

# Define metrics
api_request_count = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
api_request_latency = Histogram('api_request_latency_seconds', 'API request latency', ['endpoint'])
api_cost = Counter('api_cost_usd_total', 'Total API cost in USD', ['model', 'endpoint'])

@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    endpoint = request.url.path

    api_request_count.labels(endpoint=endpoint, status=response.status_code).inc()
    api_request_latency.labels(endpoint=endpoint).observe(duration)

    return response
```

**Cost Tracking Decorator:**
```python
# lct_python_backend/instrumentation/decorators.py

from functools import wraps
import time
from .cost_calculator import calculate_cost

def track_api_call(endpoint_name: str):
    """Decorator to track cost and performance of LLM API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            conversation_id = kwargs.get("conversation_id")

            try:
                response = await func(*args, **kwargs)

                # Calculate cost
                cost_usd = calculate_cost(
                    model=response.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )

                # Log to database
                await db.log_api_call({
                    "conversation_id": conversation_id,
                    "endpoint": endpoint_name,
                    "model": response.model,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now(),
                    "success": True
                })

                # Update Prometheus metrics
                api_cost.labels(model=response.model, endpoint=endpoint_name).inc(cost_usd)

                return response

            except Exception as e:
                # Log failure
                await db.log_api_call({
                    "conversation_id": conversation_id,
                    "endpoint": endpoint_name,
                    "timestamp": datetime.now(),
                    "success": False,
                    "error_message": str(e)
                })
                raise

        return wrapper
    return decorator
```

**Usage Example:**
```python
@track_api_call("generate_clusters")
async def generate_clusters(conversation_id: str, utterances: List[Utterance]):
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[...],
        temperature=0.5
    )
    return response
```

---

## Unit Testing Plan

### Testing Framework

**Backend (Python):**
- pytest (test framework)
- pytest-asyncio (async support)
- pytest-cov (coverage reporting)
- factory_boy (test fixtures)
- faker (test data generation)

**Frontend (TypeScript/React):**
- Vitest (test framework)
- React Testing Library (component testing)
- MSW (API mocking)
- Playwright (E2E testing)

### Coverage Targets

**By Component Type:**
- Database models: 100%
- API endpoints: 95%
- Parsers (Google Meet): 100%
- Analysis functions (bias, Simulacra): 80%
- UI components: 70%
- Integration tests: 100% critical paths

**Overall Target:** 85% code coverage

### Test Structure

**Backend Test Organization:**
```
tests/
├── unit/
│   ├── test_database_models.py
│   ├── test_google_meet_parser.py
│   ├── test_simulacra_detector.py
│   ├── test_cognitive_bias_detector.py
│   ├── test_speaker_analytics.py
│   └── test_instrumentation.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_graph_generation_pipeline.py
│   └── test_cost_tracking.py
├── e2e/
│   ├── test_full_workflow.py
│   └── test_training_data_export.py
└── fixtures/
    ├── sample_transcripts/
    ├── sample_conversations.py
    └── sample_responses.py
```

**Frontend Test Organization:**
```
src/
├── components/
│   ├── DualView/
│   │   ├── DualViewCanvas.tsx
│   │   └── DualViewCanvas.test.tsx
│   ├── NodeDetail/
│   │   ├── NodeDetailPanel.tsx
│   │   └── NodeDetailPanel.test.tsx
│   └── ...
└── tests/
    ├── integration/
    │   └── graph-interaction.test.tsx
    └── e2e/
        └── full-workflow.spec.ts
```

### Critical Test Cases

**1. Google Meet Parser Tests:**
```python
# tests/unit/test_google_meet_parser.py

def test_parse_simple_transcript(sample_transcript_text):
    """Test basic parsing of speaker-diarized transcript"""
    parser = GoogleMeetParser()
    result = parser.parse_text(sample_transcript_text)

    assert len(result.utterances) == 5
    assert result.utterances[0].speaker == "Aditya"
    assert result.utterances[0].text == "Okay, sorry."
    assert result.utterances[0].start_time == 0.0

def test_parse_multiline_utterance():
    """Test utterances spanning multiple lines"""
    text = """
    00:00:00
    Speaker A ~: This is a long utterance
    that spans multiple lines
    and should be concatenated.
    Speaker B ~: Short response.
    """
    parser = GoogleMeetParser()
    result = parser.parse_text(text)

    assert len(result.utterances) == 2
    assert "spans multiple lines" in result.utterances[0].text

def test_parse_missing_timestamps():
    """Test handling of incomplete timestamp data"""
    text = "Speaker A ~: No timestamp here.\nSpeaker B ~: Neither here."
    parser = GoogleMeetParser()
    result = parser.parse_text(text)

    # Should still parse speakers, estimate timestamps
    assert len(result.utterances) == 2
    assert result.utterances[0].start_time is not None

def test_parse_special_characters():
    """Test names with unicode, punctuation"""
    text = "José García ~: Hola!\nMary O'Brien ~: Hello."
    parser = GoogleMeetParser()
    result = parser.parse_text(text)

    assert result.utterances[0].speaker == "José García"
    assert result.utterances[1].speaker == "Mary O'Brien"

def test_parse_validation_errors():
    """Test validation catches malformed input"""
    text = "This is not a valid transcript format"
    parser = GoogleMeetParser()

    with pytest.raises(ValidationError) as exc:
        parser.parse_text(text)

    assert "No speakers detected" in str(exc.value)
```

**2. Instrumentation Tests:**
```python
# tests/unit/test_instrumentation.py

@pytest.mark.asyncio
async def test_track_api_call_decorator(mock_db, mock_openai):
    """Test that API calls are logged with correct cost"""

    @track_api_call("test_endpoint")
    async def mock_llm_call(conversation_id: str):
        return MockResponse(
            model="gpt-4",
            usage=MockUsage(prompt_tokens=100, completion_tokens=50)
        )

    await mock_llm_call(conversation_id="test-123")

    # Verify log entry created
    logs = await mock_db.get_api_call_logs("test-123")
    assert len(logs) == 1
    assert logs[0].model == "gpt-4"
    assert logs[0].total_tokens == 150
    assert logs[0].cost_usd > 0

def test_cost_calculation_gpt4():
    """Test GPT-4 cost calculation for various token counts"""
    cost = calculate_cost(
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500
    )

    # GPT-4 pricing: $0.03/1K input, $0.06/1K output
    expected = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
    assert abs(cost - expected) < 0.0001

def test_cost_alert_threshold(mock_db, mock_alert_service):
    """Test alert triggers when cost exceeds threshold"""

    # Log API calls that exceed daily threshold
    for i in range(100):
        await mock_db.log_api_call({
            "cost_usd": 1.5,  # $150 total
            "timestamp": datetime.now()
        })

    # Check alerts were triggered
    alerts = mock_alert_service.get_triggered_alerts()
    assert len(alerts) == 1
    assert alerts[0].alert_type == "high_daily_cost"
```

**3. Simulacra Detection Tests:**
```python
# tests/unit/test_simulacra_detector.py

def test_detect_level_1_object_level():
    """Test detection of factual, object-level statements"""
    detector = SimulacraDetector()

    utterances = [
        Utterance(text="The temperature is 72 degrees."),
        Utterance(text="According to the data, sales increased 15% last quarter.")
    ]

    results = detector.classify_utterances(utterances)

    assert results[0].level == SimulacraLevel.LEVEL_1
    assert results[0].confidence > 0.8
    assert results[1].level == SimulacraLevel.LEVEL_1

def test_detect_level_3_tribal_signaling():
    """Test detection of group signaling"""
    detector = SimulacraDetector()

    utterances = [
        Utterance(
            speaker="Alice",
            text="As a progressive, I believe we must stand together on this."
        )
    ]

    results = detector.classify_utterances(utterances)

    assert results[0].level == SimulacraLevel.LEVEL_3
    assert "tribal signaling" in results[0].explanation.lower()

def test_detect_ambiguous_requires_llm():
    """Test ambiguous cases fallback to LLM analysis"""
    detector = SimulacraDetector()

    utterances = [
        Utterance(text="I think we should prioritize customer satisfaction.")
    ]

    with patch('detector.llm_classify') as mock_llm:
        mock_llm.return_value = SimulacraLevel.LEVEL_2
        results = detector.classify_utterances(utterances)

    assert mock_llm.called
    assert results[0].level == SimulacraLevel.LEVEL_2
```

**4. Integration Tests:**
```python
# tests/integration/test_graph_generation_pipeline.py

@pytest.mark.asyncio
async def test_full_pipeline_transcript_to_graph():
    """
    Test complete flow from transcript to graph:
    1. Parse Google Meet transcript
    2. Generate nodes via AI
    3. Create temporal edges
    4. Generate contextual edges
    5. Assign zoom levels
    """
    # Load sample transcript
    transcript_path = "tests/fixtures/sample_transcript.txt"

    # Parse
    parser = GoogleMeetParser()
    parsed = await parser.parse_file(transcript_path)

    # Create conversation
    conversation_id = await db.create_conversation({
        "title": "Test Conversation",
        "source": "google_meet"
    })

    # Save utterances
    await db.save_utterances(conversation_id, parsed.utterances)

    # Generate graph
    graph_service = GraphGenerationService()
    await graph_service.generate_initial_graph(conversation_id)

    # Verify results
    nodes = await db.get_nodes(conversation_id)
    edges = await db.get_edges(conversation_id)

    assert len(nodes) > 0
    assert len(edges) > 0

    # Check zoom levels assigned
    zoom_levels = [node.zoom_level_visible for node in nodes]
    assert min(zoom_levels) >= 1
    assert max(zoom_levels) <= 5

    # Verify temporal edges
    temporal_edges = [e for e in edges if e.relationship_type == "temporal"]
    assert len(temporal_edges) == len(nodes) - 1  # Sequential chain

@pytest.mark.asyncio
async def test_cost_tracking_end_to_end():
    """Test all API calls logged and costs calculated"""
    conversation_id = await create_test_conversation()

    # Generate graph (makes multiple LLM calls)
    await GraphGenerationService().generate_initial_graph(conversation_id)

    # Check logs
    logs = await db.get_api_call_logs(conversation_id)

    assert len(logs) > 0

    # Verify cost calculated
    total_cost = sum(log.cost_usd for log in logs)
    assert total_cost > 0

    # Verify all required fields present
    for log in logs:
        assert log.model is not None
        assert log.total_tokens > 0
        assert log.latency_ms > 0
        assert log.timestamp is not None
```

**5. E2E Tests (Playwright):**
```typescript
// src/tests/e2e/full-workflow.spec.ts

import { test, expect } from '@playwright/test';

test('complete workflow: import → visualize → analyze → edit', async ({ page }) => {
  // 1. Navigate to app
  await page.goto('http://localhost:3000');

  // 2. Import Google Meet transcript
  await page.click('[data-testid="import-button"]');
  await page.setInputFiles('[data-testid="file-input"]', 'tests/fixtures/sample_transcript.pdf');
  await page.click('[data-testid="confirm-import"]');

  // Wait for graph generation
  await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 30000 });

  // 3. Verify dual-view layout
  const timelineView = await page.locator('[data-testid="timeline-view"]');
  const contextualView = await page.locator('[data-testid="contextual-view"]');

  await expect(timelineView).toBeVisible();
  await expect(contextualView).toBeVisible();

  // 4. Test zoom interaction
  await page.click('[data-testid="zoom-in"]');
  await page.waitForTimeout(500); // Animation

  // Verify more detailed nodes visible
  const visibleNodes = await page.locator('[data-node]').count();
  expect(visibleNodes).toBeGreaterThan(10);

  // 5. Select node and view details
  await page.click('[data-node-id="node-1"]');
  const detailPanel = await page.locator('[data-testid="node-detail-panel"]');
  await expect(detailPanel).toBeVisible();

  // 6. Enable edit mode and modify summary
  await page.click('[data-testid="toggle-edit-mode"]');
  await page.fill('[data-testid="node-summary-input"]', 'Updated summary text');
  await page.click('[data-testid="save-edit"]');

  // Verify edit saved
  await page.waitForSelector('[data-testid="edit-saved-indicator"]');

  // 7. View speaker analytics
  await page.click('[data-testid="nav-analytics"]');
  await expect(page.locator('[data-testid="speaker-analytics-view"]')).toBeVisible();

  // Verify analytics loaded
  const speakerCards = await page.locator('[data-testid="speaker-card"]').count();
  expect(speakerCards).toBeGreaterThan(0);

  // 8. Check cost tracking
  await page.click('[data-testid="nav-settings"]');
  await page.click('[data-testid="view-cost-dashboard"]');

  const totalCost = await page.textContent('[data-testid="total-cost"]');
  expect(parseFloat(totalCost)).toBeGreaterThan(0);
});

test('Simulacra level detection UI', async ({ page }) => {
  await page.goto('http://localhost:3000/conversations/test-123');

  // Enable Simulacra levels (power user feature)
  await page.click('[data-testid="settings"]');
  await page.check('[data-testid="enable-simulacra-detection"]');

  // Wait for analysis
  await page.waitForSelector('[data-testid="simulacra-indicator"]');

  // Verify level indicators visible on utterances
  const level1Indicators = await page.locator('[data-simulacra-level="1"]').count();
  const level3Indicators = await page.locator('[data-simulacra-level="3"]').count();

  expect(level1Indicators + level3Indicators).toBeGreaterThan(0);

  // Click indicator to see explanation
  await page.click('[data-simulacra-level="3"]').first();
  const explanation = await page.locator('[data-testid="simulacra-explanation"]');
  await expect(explanation).toContainText('tribal signaling');
});
```

### Continuous Integration

**GitHub Actions Workflow:**
```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd lct_python_backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests with coverage
        run: |
          cd lct_python_backend
          pytest --cov=. --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./lct_python_backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/coverage-final.json
```

**Coverage Requirements:**
```yaml
# .coveragerc (Python)
[run]
omit =
  */tests/*
  */migrations/*
  */venv/*

[report]
fail_under = 85
show_missing = True
```

```json
// package.json (JavaScript)
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 70,
        "functions": 70,
        "lines": 85,
        "statements": 85
      }
    }
  }
}
```

---

## Risk Assessment & Mitigation

### High-Priority Risks

**1. LLM API Cost Overruns**
- **Risk:** Unexpected cost spikes from inefficient prompts or high usage
- **Probability:** Medium (40%)
- **Impact:** High (budget exhaustion)
- **Mitigation:**
  - Implement strict cost tracking and alerts (Week 2)
  - Set daily/weekly spending limits
  - Use prompt caching where possible
  - A/B test prompts for cost efficiency
  - Provide cost estimates before expensive operations

**2. Poor Bias Detection Accuracy**
- **Risk:** Too many false positives frustrate users, false negatives reduce trust
- **Probability:** High (60%)
- **Impact:** Medium (feature perceived as unreliable)
- **Mitigation:**
  - Set confidence thresholds (only show high-confidence detections)
  - Allow users to provide feedback on false positives
  - Continuously improve prompts based on user feedback
  - Make feature opt-in for power users initially

**3. Performance Degradation with Large Conversations**
- **Risk:** UI becomes sluggish with 500+ nodes, long transcripts
- **Probability:** Medium (50%)
- **Impact:** High (unusable for long meetings)
- **Mitigation:**
  - Implement aggressive node culling based on zoom level
  - Use virtualization for timeline view
  - Paginate analytics queries
  - Profile and optimize rendering pipeline
  - Set realistic expectations (test with 2-hour conversations)

**4. Google Meet Parser Brittleness**
- **Risk:** Google changes transcript format, parser breaks
- **Probability:** Medium (30%)
- **Impact:** High (core feature broken)
- **Mitigation:**
  - Extensive test coverage with real transcripts
  - Graceful degradation (allow manual speaker annotation)
  - Version detection (detect format changes)
  - Support multiple input formats (PDF, TXT, manual paste)

**5. Database Migration Failures**
- **Risk:** Migration breaks production data, downtime
- **Probability:** Low (20%)
- **Impact:** Critical (data loss)
- **Mitigation:**
  - Test migrations extensively on staging
  - Full database backup before migration
  - Rollback plan documented and tested
  - Blue-green deployment strategy

### Medium-Priority Risks

**6. Edit History Storage Growth**
- **Risk:** `edits_log` table grows unbounded
- **Probability:** High (80%)
- **Impact:** Low (storage cost, query slowdown)
- **Mitigation:**
  - Partition table by conversation_id
  - Archive old edits to cold storage
  - Index optimization

**7. Prompt Engineering Complexity**
- **Risk:** Maintaining consistent prompts across features difficult
- **Probability:** Medium (50%)
- **Impact:** Medium (inconsistent results)
- **Mitigation:**
  - Centralized prompts.json configuration
  - Versioning and rollback capability
  - A/B testing framework for prompt changes

---

## Success Metrics

### MVP Launch Criteria (End of Week 14)

**Functional Requirements:**
- [ ] Import Google Meet transcripts (PDF/TXT)
- [ ] Generate graph with 5 zoom levels
- [ ] Dual-view architecture working
- [ ] Node detail panel with edit capability
- [ ] Speaker analytics view
- [ ] Cost tracking dashboard
- [ ] Edit history export

**Performance Requirements:**
- [ ] Graph generation: < 60 seconds for 1-hour conversation
- [ ] Zoom transitions: < 100ms
- [ ] UI render: 60 FPS with 100 nodes
- [ ] Parse success rate: > 90%

**Quality Requirements:**
- [ ] Test coverage: 85%+
- [ ] Zero P0 bugs
- [ ] User satisfaction: 4/5 from beta testers

**Business Requirements:**
- [ ] Cost per conversation: < $3.00
- [ ] 10 beta users onboarded
- [ ] Documentation complete

### Post-MVP Metrics (Ongoing)

**Usage Metrics:**
- Monthly active users
- Conversations created per user
- Average conversation length
- Feature adoption rates

**Quality Metrics:**
- Parse success rate (target: 95%)
- User-reported bugs per week (target: < 5)
- Edit frequency (measure: is AI good enough?)

**Cost Metrics:**
- Cost per conversation (target: < $2.00)
- Cost per user per month (target: < $10)

**Performance Metrics:**
- Graph generation time (target: < 30 seconds)
- API latency p95 (target: < 2 seconds)

---

## Appendices

### Appendix A: Technology Stack Summary

**Backend:**
- Python 3.11
- FastAPI (web framework)
- SQLAlchemy (ORM)
- Alembic (migrations)
- PostgreSQL 14
- OpenAI Python SDK
- Anthropic Python SDK
- pytest (testing)

**Frontend:**
- React 18
- TypeScript 5
- Vite (build tool)
- React Flow (graph visualization)
- TailwindCSS (styling)
- Vitest (testing)
- Playwright (E2E testing)

**Infrastructure:**
- Google Cloud Storage (file storage)
- Prometheus (metrics)
- Grafana (dashboards)
- Sentry (error tracking)
- GitHub Actions (CI/CD)

### Appendix B: Cost Estimation Details

**LLM API Costs (per 1000 conversations):**

Assumptions:
- Average conversation: 10,000 words = ~13,333 tokens
- Average generated graph: 50 nodes, 100 edges

Operations per conversation:
1. Initial clustering: 13k input + 2k output = $0.48 (GPT-4)
2. Contextual edges: 5k input + 1k output = $0.18 (GPT-3.5-turbo)
3. Speaker analytics: 10k input + 500 output = $0.33 (GPT-4)
4. Simulacra detection: 13k input + 1k output = $0.45 (GPT-4)
5. Bias detection: 13k input + 2k output = $0.51 (GPT-4)

**Total per conversation:** ~$1.95

**For 1000 conversations:** ~$1,950

**Monthly estimates (100 conversations):** ~$195

**Optimization opportunities:**
- Use GPT-3.5-turbo for simpler tasks (-50% cost)
- Implement prompt caching (-30% cost on repeated patterns)
- Batch processing where possible (-10% cost)

**Optimized cost:** ~$1.00 per conversation

### Appendix C: Database Schema Quick Reference

See `DATA_MODEL_V2.md` for full schema.

**Key Tables:**
- `conversations`: Conversation metadata
- `utterances`: Raw speaker-diarized text
- `nodes`: AI-generated summaries/chunks
- `edges`: Relationships between nodes
- `clusters`: Hierarchical groupings for zoom
- `edits_log`: Training data (all user edits)
- `api_calls_log`: Cost and performance tracking

### Appendix D: Glossary

**Terms:**
- **Utterance:** Single statement by one speaker
- **Node:** AI-generated conversation chunk (summary + utterances)
- **Edge:** Relationship between nodes (temporal or contextual)
- **Cluster:** Hierarchical grouping of nodes for zoom levels
- **Zoom Level:** Discrete granularity level (1-5)
- **Simulacra Level:** Zvi Mowshowitz framework for communication intent (1-4)
- **Cognitive Bias:** Systematic pattern of deviation from rationality
- **Implicit Frame:** Hidden worldview or assumption in normative claims

---

## Revision History

| Version | Date       | Author  | Changes                        |
|---------|------------|---------|--------------------------------|
| 1.0     | 2025-11-11 | Claude  | Initial roadmap                |

---

**End of Roadmap**
