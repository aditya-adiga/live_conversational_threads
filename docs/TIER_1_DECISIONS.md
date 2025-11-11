# Tier 1 Foundational Decisions - Live Conversational Threads

**Status**: Decided (for MVP)
**Date**: 2025-11-11
**Context**: These decisions form the foundation for all subsequent features and must be locked in before implementation.

---

## 1. Google Meet Transcript Import

### ✅ DECIDED: Input Format

**Primary format**: Google Meet transcript (PDF or TXT) with speaker diarization

**Format specification**:
```
Speaker Name ~: utterance text
Another Speaker ~: response text
```

**Example** (from actual transcript):
```
Aditya ~: Okay, sorry.
Sahil ~: One second.
Harshit Aggarwal: So, why is the thing so zoomed in on your face?
```

**Supported formats** (priority order):
1. **PDF** - Google Meet "Notes by Gemini" exports (PRIMARY)
2. **TXT** - Plain text with same speaker format
3. **Manual paste** - Copy-paste into web form

**NOT supporting initially**:
- Google Doc URL auto-fetch (OAuth complexity)
- VTT/SRT files (different use case)
- Google Meet API direct integration (not available)

### ✅ DECIDED: Speaker Attribution

**Parsing logic**:
- Regex pattern: `^([A-Za-z\s]+)\s*~?:\s*(.+)$`
- Capture groups: (1) speaker name, (2) utterance text
- Normalize speaker names: "Aditya ~" → "Aditya"
- Handle edge cases:
  - Multiple speakers in one paragraph → split by speaker prefix
  - No speaker prefix → attribute to last known speaker
  - Unknown speaker → "Unknown Speaker"

**Speaker identity**:
- No authentication/account linking for MVP
- Speakers identified purely by name string in transcript
- User can manually correct speaker attribution in UI later

---

## 2. Audio Storage & Re-transcription

### ✅ DECIDED: NO Audio Storage for MVP

**Rationale**: Too expensive to process audio as first-class primitive

**Architecture planning**:
- Design data model to **support** future audio storage
- Add optional `audio_segment_id` foreign key to `utterances` table
- Document audio re-transcription flow in ADR-001
- Don't implement audio infrastructure yet

**Future capability** (designed but not built):
```python
class AudioSegment(BaseModel):
    id: str
    conversation_id: str
    start_time: float
    end_time: float
    storage_url: str  # S3/GCS path
    format: str  # "mp3", "wav"
    retention_policy: str  # "30_days", "forever", etc.

class Utterance(BaseModel):
    # ... existing fields ...
    audio_segment_id: Optional[str] = None  # FK to AudioSegment
```

**Transcript is source of truth for MVP** - all corrections happen at text level

---

## 3. Edit Mode & Correction Scope

### ✅ DECIDED: Edit ONLY Graph Nodes, NOT Raw Transcript

**What users CAN edit**:
1. **Node summaries** - The AI-generated text description of each node
2. **Node boundaries** - Merge/split nodes, change which utterances belong to which node
3. **Edges** - Add/remove/relabel relationships between nodes
4. **Node metadata**:
   - Is bookmark? (cyan color)
   - Is contextual progress? (green color)
   - Custom labels/tags
5. **Zoom-level granularity** - "This section needs more/fewer nodes"

**What users CANNOT edit** (for MVP):
- ❌ Raw transcript text (utterances remain as-is from Google Meet)
- ❌ Speaker attribution (fixed from import, unless we add manual override later)
- ❌ Timestamps (from transcript)

**Why not edit raw transcript?**
- Scope creep - transcript editing is a separate complex feature
- Google Meet transcripts are already "pretty good" (Gemini-powered)
- Focus on **graph-level corrections** where AI needs most help
- Can add transcript editing in future if needed

### ✅ DECIDED: Who Can Edit

**For MVP**: Single-user editing
- The person who uploads the transcript is the "owner"
- Only owner can edit the graph
- No multi-user permissions system initially

**Editing workflow**:
1. User uploads transcript → AI generates initial graph
2. User reviews graph in view mode
3. User switches to "Edit Mode" (button/toggle)
4. User makes corrections to nodes/edges
5. User saves corrections → stored in database
6. Corrections used as training data for future AI improvements

**Future**: Multi-user with roles
- Participants can edit their own nodes
- Moderator can edit everything
- View-only guests
- (Not implementing yet)

---

## 4. Coarse-Graining & Multi-Scale Visualization

### ✅ DECIDED: Prompt Engineering Approach (Not Algorithmic)

**Core idea**: Treat AI as "general intelligence" that understands zoom context

**Architecture**:

```
User Action: Zoom out to 50%
    ↓
Frontend calculates: screen_width, screen_height, zoom_level
    ↓
Backend receives: {
  "current_graph": [...nodes, edges...],
  "zoom_level": 0.5,
  "viewport": {"width": 1920, "height": 1080}
}
    ↓
Prompt to LLM:
"You have a conversation graph with 50 nodes. The viewport is 1920x1080.
The user zoomed out to 50%. Currently nodes are cluttered.
Please group related topical nodes into clusters and return a DIFF:
- clusters_to_create: [{id, label, child_node_ids}]
- nodes_to_hide: [node_ids]
- nodes_to_show: [node_ids]
- edges_to_update: [{from, to, label}]"
    ↓
LLM returns JSON diff
    ↓
Frontend applies diff incrementally (no full re-render)
```

**Why prompt engineering over algorithms**:
- **Flexibility**: Can handle semantic similarity, speaker transitions, topic shifts
- **Context-aware**: AI understands "this is a digression" vs "this is main thread"
- **Token efficiency**: Diffs are much smaller than full graph re-generation
- **Iterative**: User can reject cluster and AI tries again

**Diff-based communication** (minimize token cost):
```json
{
  "add_cluster": {
    "id": "cluster_1",
    "label": "Guest Invites Discussion",
    "child_nodes": ["node_3", "node_4", "node_5"],
    "position": {"x": 100, "y": 200}
  },
  "hide_nodes": ["node_3", "node_4", "node_5"],
  "show_nodes": ["cluster_1"]
}
```

**NOT doing initially**:
- ❌ Pre-computed hierarchies (too rigid)
- ❌ Algorithmic clustering (k-means, community detection - loses semantic meaning)
- ❌ Fixed zoom levels (want continuous zoom)

### ✅ DECIDED: Bidirectional (Fine + Coarse)

**Zoom IN (fine-graining)**:
- Click cluster → AI expands into child nodes
- Diff: `hide_cluster`, `show_child_nodes`

**Zoom OUT (coarse-graining)**:
- AI groups nodes into clusters
- Diff: `create_cluster`, `hide_nodes`

**Continuous zoom slider**:
- Triggers re-clustering at threshold zoom levels
- Example: 100% (all nodes) → 75% (light clustering) → 50% (heavy clustering) → 25% (only main threads)

---

## 5. Data Model Implications

### Core Tables (Updated for Tier 1 Decisions)

```sql
-- Existing tables from current app
conversations (
  id, name, created_at, metadata
)

utterances (  -- NEW TABLE
  id,
  conversation_id FK,
  speaker_name TEXT,  -- "Aditya", "Sahil", etc.
  text TEXT,
  start_time FLOAT,  -- seconds from start
  end_time FLOAT,
  audio_segment_id UUID NULL  -- future: FK to audio_segments
)

nodes (  -- Rename from chunks
  id,
  conversation_id FK,
  summary TEXT,  -- AI-generated, user-editable
  node_type ENUM('regular', 'bookmark', 'contextual_progress'),
  utterance_ids JSON,  -- Array of utterance IDs in this node
  created_by ENUM('ai', 'user'),
  edited BOOLEAN DEFAULT FALSE,
  zoom_level_visible FLOAT,  -- 0.0-1.0, minimum zoom to show this node
  position JSON  -- {x, y} for graph layout
)

edges (
  id,
  conversation_id FK,
  from_node_id FK,
  to_node_id FK,
  relationship_type ENUM('temporal', 'contextual'),
  label TEXT,  -- "next", "contradicts", "supports", etc.
  created_by ENUM('ai', 'user'),
  edited BOOLEAN DEFAULT FALSE
)

clusters (  -- NEW TABLE for zoom levels
  id,
  conversation_id FK,
  label TEXT,  -- "Guest Invites Discussion"
  child_node_ids JSON,  -- Array of node IDs
  zoom_level_min FLOAT,  -- Only visible between these zoom levels
  zoom_level_max FLOAT,
  position JSON
)

edits_log (  -- NEW TABLE for training data
  id,
  conversation_id FK,
  user_id FK,
  edit_type ENUM('node_summary', 'node_merge', 'node_split', 'edge_add', 'edge_remove', 'cluster_create'),
  before_value JSON,
  after_value JSON,
  timestamp TIMESTAMP,
  feedback TEXT  -- Optional: why user made this change
)
```

### Migration from Current Schema

**Current schema** (from codebase review):
- `graph_data`: Array of nodes with predecessors/successors
- `chunk_dict`: Dictionary of node names to content

**Migration plan**:
1. Keep `graph_data` and `chunk_dict` for backward compatibility
2. Add new tables: `utterances`, `clusters`, `edits_log`
3. Parse transcript → populate `utterances` table
4. Generate nodes from `chunk_dict` → populate `nodes` table with `utterance_ids`
5. Future imports use new schema; old conversations read from legacy format

---

## 6. Implementation Priorities

### Phase 1: Transcript Import (Week 1)
- [ ] PDF parser for Google Meet format
- [ ] Speaker name extraction (regex)
- [ ] Populate `utterances` table
- [ ] Basic utterance → node grouping (time-based chunking initially)

### Phase 2: Edit Mode (Week 2)
- [ ] UI toggle: View Mode ↔ Edit Mode
- [ ] Edit node summary (textarea)
- [ ] Edit edge label (inline edit)
- [ ] Save edits to `edits_log`
- [ ] Display "edited" indicator on nodes

### Phase 3: Zoom/Cluster (Week 3-4)
- [ ] Zoom slider component
- [ ] Backend: Prompt engineering for clustering
- [ ] Diff application on frontend (add/hide nodes)
- [ ] Persist cluster definitions

### Phase 4: Training Loop (Week 5)
- [ ] Export `edits_log` to training format
- [ ] Analyze correction patterns
- [ ] Update prompts based on corrections
- [ ] (Future: Fine-tune model)

---

## 7. Open Questions (For Tier 2)

These are **deferred** but documented:

### Permissions
- Q: Should participants be able to see the graph of conversations they're in?
- Q: Privacy controls for sensitive conversations?

### Thread Detection
- Q: How to detect when a topic is "paused" vs "completed"?
- Q: Automatic or manual thread tagging?

### Claim Taxonomy
- Q: Should AI auto-classify claims as factual/normative/worldview?
- Q: How to show dependency chains in UI?

### Bandwidth Metrics
- Q: Show speaker stats during review or live during conversation?
- Q: What's a "good" balance? Equal time or context-dependent?

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Prompt-based clustering is too slow (>2s latency) | Medium | High | Cache clusters per zoom level; use streaming responses |
| Users reject AI clustering suggestions | High | Medium | Always allow manual override; learn from rejections |
| Diff-based updates create inconsistent state | Low | High | Validate diffs server-side; add rollback mechanism |
| Google Meet transcript format changes | Low | Medium | Version PDF parser; add fallback to manual correction |
| Token costs explode with long conversations | Medium | High | Cap conversation length at 2 hours (typical meeting); paginate very long convos |

---

## 9. Success Metrics

**MVP success = answering these questions**:

1. **Transcript parsing accuracy**: >95% of utterances correctly attributed to speakers
2. **Node edit rate**: What % of AI-generated nodes need correction? (Target: <20%)
3. **Clustering usefulness**: Do users actually use zoom, or stay at one level? (Target: >50% zoom interaction)
4. **Edit→improvement loop**: Do corrections improve AI performance on next import? (Qualitative assessment)
5. **User satisfaction**: Post-review survey: "Did editing the graph help you understand the conversation?" (Target: >70% yes)

---

## 10. What We're NOT Doing (Anti-Scope)

To prevent scope creep:

- ❌ Live real-time conversation graphing (stays async/post-hoc)
- ❌ Audio storage/processing
- ❌ Multi-format transcript ingestion (VTT, SRT, etc.)
- ❌ Algorithmic clustering (k-means, modularity)
- ❌ Fine-tuning custom models (just prompt engineering)
- ❌ Multi-user collaborative editing
- ❌ Fact-checking integration (Tier 2)
- ❌ Goal tracking (Tier 2)
- ❌ Bandwidth metrics (Tier 2)

---

## Next Steps

1. **Review this document** - confirm all Tier 1 decisions are correct
2. **Update ADR-001** to reflect these decisions
3. **Update DATA_MODEL_V2.md** with final schema
4. **Create implementation tickets** for Phase 1-4
5. **Schedule EGP** to surface additional questions

---

## 11. Zoom Level Granularity (UPDATED)

### ✅ DECIDED: Topic-Based Node Generation (NOT Time-Based)

**Node granularity levels** (quantized into 3-4 discrete zoom levels):

```
Level 5 (EXTREME ZOOM IN): Sentence/word-level
├─ Each sentence becomes a node
├─ Can decompose further into word relationships
└─ Show etymology, root words, linguistic structure

Level 4 (FINE): Speaker turn-based
├─ Each speaking turn becomes a node cluster
└─ Decompose long monologues into sentences

Level 3 (MEDIUM - DEFAULT): Topic shifts
├─ AI detects semantic topic boundaries
└─ This is the default view on import

Level 2 (COARSE): Major themes
├─ Related topics grouped into themes
└─ Good for 30-60 min conversations

Level 1 (EXTREME ZOOM OUT): Narrative arcs / Chapters
├─ Conversation divided into major "acts"
└─ Natural topic boundaries for pagination of long conversations (>2 hours)
```

**Implementation strategy**:
- Pre-compute Levels 1-4 on import (cache results)
- Compute Level 5 on-demand (expensive, rarely used)
- Use AI to find natural "chapter" boundaries for >2 hour conversations

**Why not time-based?**
> "Time is just arbitrary objective numbers. What really matters is the rhythm of the conversation. We can use intelligence to handle that."

---

## 12. Node Detail Panel Architecture (UPDATED)

### ✅ DECIDED: Split Screen with Zoom-Dependent Context

**Layout**: Split screen (Option C)
- Graph view on left
- Detail panel on right
- Works on tablets

**Context display logic** (depends on zoom level):

```python
if zoom_level >= 0.8:  # Very zoomed in (sentence/word level)
    # Show previous notes and context
    display_context = {
        "previous_nodes": 2,  # Show 2 nodes before
        "next_nodes": 2,      # Show 2 nodes after
        "mode": "detailed"
    }
elif zoom_level < 0.3:  # Very zoomed out (narrative arc level)
    # Show summary of entire thread
    display_context = {
        "mode": "summary",
        "summary_of": "entire_thread_arc"
    }
else:  # Medium zoom
    # Show just this node's context
    display_context = {
        "mode": "focused",
        "previous_nodes": 1,
        "next_nodes": 1
    }
```

**Detail panel sections** (stacked, collapsible):
1. **Transcript & Context** (always visible)
2. **Edges & Dependencies** (collapsible, shows mini-graph)
3. **Factual Claims** (collapsible, extracted but not fact-checked yet)
4. **Structural Issues** (collapsible, fallacy/bias detection - on-demand)

### ✅ DECIDED: Edit Mode Toggle Required

**UX Friction is intentional**:
- User must explicitly click "Edit Mode" toggle to make changes
- Prevents accidental edits
- Clear separation between review and editing workflows

---

## 13. Dual-View Architecture (CRITICAL UPDATE)

### ✅ DECIDED: Timeline + Contextual Views BOTH Visible (NOT Toggleable)

**Layout**:
```
┌─────────────────────────────────────────┐
│                                         │
│      CONTEXTUAL VIEW (Top - Main)       │
│   Network layout, semantic clusters     │
│                                         │
├─────────────────────────────────────────┤
│ TIMELINE VIEW (Bottom - Thin Strip)    │
│ [Node1]─→[Node2]─→[Node3]─→[Node4]     │
└─────────────────────────────────────────┘
```

**How it works**:
- **Timeline view** (bottom): Linear left-to-right chronological layout
  - Shows temporal sequence (A → B → C)
  - Thin strip, ~15% of screen height
  - Only temporal edges visible

- **Contextual view** (top): Network/cluster layout
  - Shows semantic relationships (supports, contradicts, related_to)
  - Main focus area, ~85% of screen height
  - Force-directed or hierarchical layout

- **Linked highlighting**: Click node in one view → highlights in both views
- **1:1 correspondence**: Same nodes in both views, different layouts
- **Zoom affects both**: Coarse-graining changes which nodes appear in both views simultaneously

**Already partially implemented** in current codebase - extend this pattern!

---

## 14. User Answers to All Open Questions

### Node Granularity
✅ **Topic-based** (NOT time-based) with 5 discrete zoom levels

### Node Detail Panel
✅ **Split screen** layout, context depends on zoom level

### Edit Mode
✅ **Toggle required** (UX friction intentional)

### Fallacy Detection
✅ **On-demand** (not always running)
✅ **Bidirectional feedback** (user can dismiss/override - critical for training)

### Fact-Checking
✅ **Extract claims only** (no auto fact-check for MVP)
✅ Future: on-demand via Perplexity/other APIs

### Normative Claims & Frames
✅ **Future iteration**: Detect "Simulacra levels" and implicit frames
✅ Example: "preserve light of consciousness" → sneaky normative claim
✅ User will provide context document on Simulacra levels

### Speaker Analytics
✅ **Separate Analytics VIEW** (not sidebar)
✅ Focus on: speaker roles (grounding, deconstructing, constructing)
✅ Timestamp calculation: Option B (parse precisely)
✅ Topic tagging: Use node summaries + few-shot prompting

### Temporal vs Contextual Views
✅ **Both visible simultaneously** (timeline at bottom, contextual on top)
✅ NOT toggleable - always see both
✅ Linked highlighting between views

### Custom Edges
✅ **3 standard types** for MVP: supports, contradicts, related_to
✅ **Top 3 AI suggestions** per node (low opacity → user promotes)

### Edit History
✅ **Optional user notes** (not required)
✅ **Visible in settings** (collapsible)
✅ **Power users** can enable/disable all features

---

## 15. New Infrastructure Requirements

### Prompts Configuration System
- **JSON file** with all prompts (user-editable)
- Settings page to modify prompts per API call
- Version control for prompt changes
- Few-shot examples for topic tagging

### Instrumentation & Cost Tracking
**Metrics to track** (per API call):
- **Time taken** (latency in ms)
- **Cost** (tokens used × model pricing)
- **Model used** (e.g., GPT-4, Claude Sonnet)

**Settings page features**:
- Model selection dropdown
- Credit limit warnings
- Spending dashboard
- Performance metrics graph

---

## 16. Updated Anti-Scope

Adding to "What We're NOT Doing":

- ❌ Auto fact-checking (future: on-demand only)
- ❌ Simulacra level detection (future iteration after user provides context)
- ❌ Sidebar analytics (using separate view instead)
- ❌ Toggleable view switching (both views always visible)

---

**All Tier 1 questions answered ✅**
**Ready to proceed with Tier 2 feature specs**
