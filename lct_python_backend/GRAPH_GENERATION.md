# Graph Generation Service

**Version:** 1.0
**Status:** Implemented (Week 4)
**Last Updated:** 2025-11-11

## Overview

The Graph Generation Service transforms parsed conversation transcripts into hierarchical, multi-zoom-level graph structures using AI-powered analysis. The system automatically:

- **Identifies topic boundaries** at 5 different zoom levels (SENTENCE → TURN → TOPIC → THEME → ARC)
- **Creates nodes** representing conversational segments with summaries and metadata
- **Generates temporal edges** connecting sequential conversation flow
- **Detects contextual relationships** between thematically related nodes
- **Calculates zoom distributions** for optimal visualization
- **Tracks costs** for all LLM API calls

---

## Quick Start

### 1. Generate Graph from Conversation

```bash
curl -X POST "http://localhost:8000/api/graph/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "use_llm": true,
    "model": "gpt-4"
  }'
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "node_count": 12,
  "edge_count": 15,
  "zoom_distribution": {
    "1": 3,
    "2": 4,
    "3": 5,
    "4": 3,
    "5": 1
  },
  "generation_time_seconds": 8.4,
  "llm_cost": 0.15
}
```

### 2. Retrieve Generated Graph

```bash
curl "http://localhost:8000/api/graph/550e8400-e29b-41d4-a716-446655440000?zoom_level=3"
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "nodes": [
    {
      "id": "node_uuid_1",
      "title": "Project Timeline Discussion",
      "summary": "Team discusses Q1 deadline and milestone planning",
      "zoom_level_visible": [3, 4, 5],
      "utterance_ids": ["utt_1", "utt_2", "utt_3"],
      "speaker_info": {
        "primary_speaker": "Alice",
        "secondary_speakers": ["Bob"]
      },
      "keywords": ["timeline", "Q1", "deadline"],
      "canvas_x": 100,
      "canvas_y": 200
    }
  ],
  "edges": [
    {
      "id": "edge_uuid_1",
      "source_node_id": "node_uuid_1",
      "target_node_id": "node_uuid_2",
      "relationship_type": "temporal",
      "strength": 1.0
    }
  ],
  "node_count": 12,
  "edge_count": 15
}
```

---

## Architecture

### The 5-Level Zoom System

The graph generation system creates nodes at 5 different granularity levels to enable multi-scale exploration:

| Level | Name     | Description                                  | Typical Size        |
|-------|----------|----------------------------------------------|---------------------|
| 1     | SENTENCE | Individual important sentences/short exchanges| 1-2 utterances      |
| 2     | TURN     | Speaker turns or complete thoughts           | 2-5 utterances      |
| 3     | TOPIC    | Distinct topics or sub-discussions           | 3-10 utterances     |
| 4     | THEME    | Major themes or discussion areas             | 10-30 utterances    |
| 5     | ARC      | Overall narrative arcs or meeting segments   | 30+ utterances      |

**Example:**
```
Level 5 (ARC): "Product Launch Planning Meeting"
  ├─ Level 4 (THEME): "Timeline and Deadlines"
  │   ├─ Level 3 (TOPIC): "Q1 Goals Discussion"
  │   │   ├─ Level 2 (TURN): "Alice proposes March deadline"
  │   │   └─ Level 2 (TURN): "Bob raises concerns about capacity"
  │   └─ Level 3 (TOPIC): "Milestone Definition"
  └─ Level 4 (THEME): "Budget Allocation"
      └─ Level 3 (TOPIC): "Resource Requirements"
```

### Graph Structure

**Nodes:**
- Represent conversational segments (topics, themes, utterances)
- Contain: title, summary, keywords, speaker info, position
- Visible at one or more zoom levels
- Link to specific utterances in the conversation

**Edges:**
- **Temporal**: Sequential conversation flow (A → B in time)
- **Contextual**: Thematic relationships (shared topics, cause-effect, references)
- Have strength values (0.0-1.0) and descriptive labels

---

## Generation Workflow

### Phase 1: Initial Clustering

**LLM Prompt:** `initial_clustering`
**Model:** GPT-4
**Purpose:** Identify natural topic boundaries and create nodes

```python
from services import GraphGenerationService
from parsers import GoogleMeetParser

# Parse transcript
parser = GoogleMeetParser()
transcript = parser.parse_file("meeting.pdf")

# Generate graph
service = GraphGenerationService(llm_client=openai_client, db=db)
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    save_to_db=True,
)
```

**What happens:**
1. Transcript formatted for LLM: `"[0] Alice: Let's discuss the timeline\n[1] Bob: I think Q1 is realistic\n..."`
2. LLM analyzes and identifies topic boundaries
3. Returns JSON array of nodes with metadata
4. Service validates and stores nodes

**LLM Output Example:**
```json
[
  {
    "title": "Opening and Introductions",
    "summary": "Team greets each other and Alice opens meeting",
    "zoom_levels": [3, 4, 5],
    "start_utterance": 0,
    "end_utterance": 5,
    "primary_speaker": "Alice",
    "keywords": ["greeting", "introduction", "meeting start"]
  },
  {
    "title": "Timeline Discussion",
    "summary": "Discussion of Q1 deadline and key milestones",
    "zoom_levels": [2, 3, 4],
    "start_utterance": 6,
    "end_utterance": 15,
    "primary_speaker": "Bob",
    "keywords": ["timeline", "Q1", "deadline", "milestones"]
  }
]
```

### Phase 2: Temporal Edge Creation

**Purpose:** Connect nodes in chronological order

Automatically creates edges between sequential nodes:
- `node[i] --temporal--> node[i+1]`
- Strength: 1.0 (guaranteed sequential flow)

```python
edges = service._create_temporal_edges(nodes)
# Result: [
#   {"source": "node_1", "target": "node_2", "type": "temporal", "strength": 1.0},
#   {"source": "node_2", "target": "node_3", "type": "temporal", "strength": 1.0},
# ]
```

### Phase 3: Contextual Relationship Detection

**LLM Prompt:** `detect_contextual_relationships`
**Model:** GPT-4
**Purpose:** Find thematic connections between non-sequential nodes

Identifies relationships based on:
- **Shared themes**: Both discuss "budget" or "timeline"
- **References**: Later node refers back to earlier topic
- **Cause-effect**: Decision in node A leads to discussion in node B
- **Question-answer**: Question in node A answered in node C
- **Elaboration**: Node B expands on idea from node A
- **Contrast**: Node B presents opposing view to node A

**Example:**
```json
[
  {
    "source_node_id": "node_3",
    "target_node_id": "node_7",
    "relationship_type": "theme",
    "strength": 0.8,
    "description": "Both nodes discuss timeline and deadlines"
  },
  {
    "source_node_id": "node_2",
    "target_node_id": "node_9",
    "relationship_type": "reference",
    "strength": 0.9,
    "description": "Node 9 refers back to budget concerns raised in Node 2"
  }
]
```

### Fallback Mode (No LLM)

When LLM is unavailable or disabled, the service uses heuristic-based generation:

**Node Creation:**
- Group utterances into fixed-size chunks (5 utterances per node)
- Generate simple titles: "Segment 1", "Segment 2"
- Extract first sentence as summary
- Identify primary speaker (most utterances in segment)

**Edge Creation:**
- Temporal edges (always)
- Keyword-based relationships (Jaccard similarity > 0.3)

```python
service = GraphGenerationService(llm_client=None, db=db)
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    use_llm=False,  # Explicit fallback
)
```

---

## LLM Prompts Reference

### 1. initial_clustering

**Purpose:** Generate topic-based nodes from transcript
**Model:** GPT-4
**Temperature:** 0.5
**Max Tokens:** 4000

**Input Variables:**
- `{utterance_count}`: Number of utterances
- `{participant_count}`: Number of speakers
- `{participants}`: Comma-separated speaker names
- `{transcript}`: Formatted conversation text

**Output:** JSON array of nodes

### 2. detect_contextual_relationships

**Purpose:** Identify thematic relationships between nodes
**Model:** GPT-4
**Temperature:** 0.3
**Max Tokens:** 2000

**Input Variables:**
- `{nodes_json}`: JSON string of all nodes

**Constraints:**
- Max 5 relationships per node
- Minimum strength: 0.5

**Output:** JSON array of relationships

### 3. refine_node_summary

**Purpose:** Generate or improve node summary
**Model:** GPT-4
**Temperature:** 0.7
**Max Tokens:** 500

**Input Variables:**
- `{utterances_text}`: Utterances in the node

**Output:** Plain text summary (1-3 sentences)

### 4. extract_keywords

**Purpose:** Extract key terms from text
**Model:** GPT-3.5-turbo
**Temperature:** 0.3
**Max Tokens:** 200

**Input Variables:**
- `{text}`: Text to analyze

**Output:** JSON array of strings (3-5 keywords)

### 5. identify_speakers_in_segment

**Purpose:** Identify primary/secondary speakers
**Model:** GPT-3.5-turbo
**Temperature:** 0.2
**Max Tokens:** 300

**Input Variables:**
- `{utterances_text}`: Segment utterances

**Output:** JSON object with speakers and transitions

### 6. suggest_zoom_levels

**Purpose:** Recommend appropriate zoom levels
**Model:** GPT-3.5-turbo
**Temperature:** 0.2
**Max Tokens:** 100

**Input Variables:**
- `{utterance_count}`: Node size
- `{importance}`: Importance score
- `{granularity}`: Granularity level

**Output:** JSON array of integers [1-5]

---

## API Reference

### POST /api/graph/generate

Generate a graph from a conversation transcript.

**Request:**
```json
{
  "conversation_id": "uuid",
  "use_llm": true,
  "model": "gpt-4",
  "detect_relationships": true
}
```

**Parameters:**
- `conversation_id` (required): UUID of conversation
- `use_llm` (optional): Use LLM or fallback (default: true)
- `model` (optional): LLM model to use (default: "gpt-4")
- `detect_relationships` (optional): Detect contextual edges (default: true)

**Response:** `GraphGenerationStatusResponse`

### GET /api/graph/{conversation_id}

Retrieve generated graph with optional zoom filtering.

**Query Parameters:**
- `zoom_level` (optional): Filter nodes by zoom level (1-5)
- `include_edges` (optional): Include edges (default: true)

**Response:** `GraphResponse`

### GET /api/graph/{conversation_id}/nodes

Get only nodes for a conversation.

**Query Parameters:**
- `zoom_level` (optional): Filter by zoom level

**Response:**
```json
{
  "conversation_id": "uuid",
  "nodes": [...],
  "node_count": 12
}
```

### GET /api/graph/{conversation_id}/edges

Get only edges for a conversation.

**Query Parameters:**
- `relationship_type` (optional): Filter by type ("temporal", "contextual")

**Response:**
```json
{
  "conversation_id": "uuid",
  "edges": [...],
  "edge_count": 15
}
```

### DELETE /api/graph/{conversation_id}

Delete generated graph for a conversation.

**Response:**
```json
{
  "success": true,
  "message": "Graph deleted for conversation uuid"
}
```

---

## Programmatic Usage

### Basic Graph Generation

```python
from services import GraphGenerationService, PromptLoader
from parsers import GoogleMeetParser
import openai

# Initialize components
parser = GoogleMeetParser()
loader = PromptLoader()
service = GraphGenerationService(llm_client=openai, db=db)

# Parse and generate
transcript = parser.parse_file("meeting.pdf")
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    save_to_db=True,
)

print(f"Generated {graph['node_count']} nodes and {graph['edge_count']} edges")
```

### Custom Prompt Rendering

```python
from services import PromptLoader

loader = PromptLoader()

# Render a prompt with variables
rendered = loader.render_template(
    "initial_clustering",
    utterance_count=50,
    participant_count=5,
    participants="Alice, Bob, Charlie, Diana, Eve",
    transcript="[0] Alice: Let's begin...\n[1] Bob: Sounds good...",
)

print(rendered)
# Uses the prompt for LLM API call
```

### Working with Nodes and Edges

```python
# Access generated nodes
for node in graph["nodes"]:
    print(f"{node['title']} (zoom: {node['zoom_level_visible']})")
    print(f"  Summary: {node['summary']}")
    print(f"  Speaker: {node['speaker_info']['primary_speaker']}")
    print(f"  Keywords: {', '.join(node['keywords'])}")
    print()

# Access edges
temporal_edges = [e for e in graph["edges"] if e["relationship_type"] == "temporal"]
contextual_edges = [e for e in graph["edges"] if e["relationship_type"] != "temporal"]

print(f"Temporal edges: {len(temporal_edges)}")
print(f"Contextual edges: {len(contextual_edges)}")
```

### Zoom Level Filtering

```python
# Get only high-level nodes (themes and arcs)
high_level_nodes = [
    node for node in graph["nodes"]
    if any(level >= 4 for level in node["zoom_level_visible"])
]

# Get granular detail nodes
detail_nodes = [
    node for node in graph["nodes"]
    if 1 in node["zoom_level_visible"] or 2 in node["zoom_level_visible"]
]
```

### Cost Tracking

```python
from instrumentation import CostCalculator

calculator = CostCalculator()

# Check cost for prompt
prompt_cost = calculator.estimate_prompt_cost(
    model="gpt-4",
    input_text=rendered_prompt,
    expected_output_tokens=1000,
)

print(f"Estimated cost: ${prompt_cost:.4f}")

# Track actual usage
api_call = await service.generate_graph(...)
# Automatically logged to api_calls_log table with actual cost
```

---

## Data Models

### Node

```python
{
  "id": UUID,
  "conversation_id": UUID,
  "title": str,
  "summary": str,
  "level": int,  # Hierarchy depth (1 = root)
  "parent_id": Optional[UUID],
  "children_ids": List[UUID],
  "zoom_level_visible": List[int],  # [1, 2, 3, 4, 5]
  "utterance_ids": List[UUID],
  "speaker_info": {
    "primary_speaker": str,
    "secondary_speakers": List[str],
    "speaker_transitions": List[Dict]
  },
  "keywords": List[str],
  "canvas_x": Optional[int],
  "canvas_y": Optional[int],
  "embedding_vector": Optional[List[float]],
  "created_at": datetime
}
```

### Edge (Relationship)

```python
{
  "id": UUID,
  "conversation_id": UUID,
  "source_node_id": UUID,
  "target_node_id": UUID,
  "relationship_type": str,  # temporal, theme, reference, etc.
  "strength": float,  # 0.0-1.0
  "description": Optional[str],
  "metadata": Dict,
  "created_at": datetime
}
```

### GraphResponse

```python
{
  "conversation_id": str,
  "nodes": List[Node],
  "edges": List[Edge],
  "node_count": int,
  "edge_count": int,
  "metadata": {
    "zoom_level_distribution": Dict[int, int],
    "relationship_type_counts": Dict[str, int],
    "generation_timestamp": str
  }
}
```

---

## Cost Optimization

### Strategy 1: Use Appropriate Models

```python
# Expensive but high-quality clustering
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    model="gpt-4",  # $0.03/1K input, $0.06/1K output
)

# Cheaper for simple conversations
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    model="gpt-3.5-turbo",  # $0.0005/1K input, $0.0015/1K output
)
```

**Cost comparison for 50-utterance conversation:**
- GPT-4: ~$0.12-0.20
- GPT-3.5-turbo: ~$0.01-0.02

### Strategy 2: Disable Contextual Relationship Detection

```python
# Skip expensive relationship detection
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
    detect_relationships=False,  # Saves ~30-50% cost
)
```

### Strategy 3: Use Fallback Mode

```python
# No LLM calls at all
service = GraphGenerationService(llm_client=None, db=db)
graph = await service.generate_graph(
    conversation_id="conv-123",
    transcript=transcript,
)
# Cost: $0.00 (but lower quality)
```

### Strategy 4: Batch Processing

```python
# Process multiple conversations in one session
conversations = [...]
for conv_id, transcript in conversations:
    graph = await service.generate_graph(
        conversation_id=conv_id,
        transcript=transcript,
    )
    # Connection overhead amortized across batch
```

### Cost Monitoring

```python
# Check daily cost
from instrumentation import CostAggregator

aggregator = CostAggregator(db)
daily_cost = await aggregator.get_daily_cost()

if daily_cost > 10.00:
    print("⚠️ Daily budget exceeded!")
    # Switch to fallback mode
    service = GraphGenerationService(llm_client=None, db=db)
```

---

## Performance

### Processing Times

| Transcript Size | LLM Mode | Fallback Mode | Cost (GPT-4) |
|----------------|----------|---------------|--------------|
| 10 utterances  | ~3s      | <0.1s         | $0.03        |
| 50 utterances  | ~8s      | ~0.2s         | $0.15        |
| 100 utterances | ~15s     | ~0.4s         | $0.30        |
| 500 utterances | ~60s     | ~1.5s         | $1.50        |

### Memory Usage

- **Base service:** ~15 MB
- **Per node:** ~2 KB
- **Large graph (500 nodes):** ~20 MB total

### Scalability

- **Max utterances:** 10,000 per conversation
- **Max nodes:** ~2,000 per graph
- **Concurrent generations:** 10+ (with connection pooling)

---

## Best Practices

### 1. Preview Before Generating

```python
# Check transcript quality first
from parsers import GoogleMeetParser

parser = GoogleMeetParser()
transcript = parser.parse_file("meeting.pdf")
validation = parser.validate_transcript(transcript)

if not validation.is_valid:
    print("❌ Cannot generate graph from invalid transcript")
    return

if validation.warnings:
    print("⚠️ Warnings:", validation.warnings)

# Proceed with generation
graph = await service.generate_graph(conversation_id, transcript)
```

### 2. Monitor Costs in Production

```python
from instrumentation import AlertManager, AlertRule

# Set up cost alerts
alert_manager = AlertManager(db)
await alert_manager.add_rule(AlertRule(
    name="daily_budget",
    threshold_type="daily_cost",
    threshold_value=50.0,
    cooldown_minutes=60,
))

# Check before each generation
alerts = await alert_manager.check_alerts()
if any(a.is_critical for a in alerts):
    # Use fallback mode or stop generation
    service = GraphGenerationService(llm_client=None, db=db)
```

### 3. Cache Graphs

```python
# Check if graph already exists
existing_graph = await db.fetch_graph(conversation_id)

if existing_graph:
    print("Using cached graph")
    return existing_graph

# Generate only if not cached
graph = await service.generate_graph(conversation_id, transcript)
```

### 4. Validate Generated Graphs

```python
graph = await service.generate_graph(conversation_id, transcript)

# Validate structure
assert graph["node_count"] > 0, "Graph must have nodes"
assert graph["edge_count"] >= graph["node_count"] - 1, "Must have temporal edges"

# Validate zoom distribution
distribution = graph["metadata"]["zoom_level_distribution"]
assert sum(distribution.values()) == graph["node_count"], "All nodes must have zoom levels"

# Validate edges reference valid nodes
node_ids = {n["id"] for n in graph["nodes"]}
for edge in graph["edges"]:
    assert edge["source_node_id"] in node_ids
    assert edge["target_node_id"] in node_ids
```

### 5. Handle LLM Failures Gracefully

```python
try:
    graph = await service.generate_graph(
        conversation_id=conv_id,
        transcript=transcript,
        use_llm=True,
    )
except openai.error.RateLimitError:
    print("Rate limit hit, using fallback")
    service_fallback = GraphGenerationService(llm_client=None, db=db)
    graph = await service_fallback.generate_graph(
        conversation_id=conv_id,
        transcript=transcript,
    )
except Exception as e:
    print(f"Error: {e}")
    # Log error and notify admin
```

---

## Troubleshooting

### Issue: "No nodes generated"

**Symptoms:** Graph has 0 nodes

**Causes:**
- Empty transcript
- LLM returned invalid JSON
- All utterances filtered out

**Solutions:**
```python
# Check transcript
if len(transcript.utterances) == 0:
    print("❌ Empty transcript")
    return

# Check LLM response
try:
    graph = await service.generate_graph(...)
except ValueError as e:
    print(f"LLM error: {e}")
    # Fall back to heuristic mode
    service = GraphGenerationService(llm_client=None, db=db)
    graph = await service.generate_graph(...)
```

### Issue: "Too many nodes generated"

**Symptoms:** Graph has 500+ nodes for 100 utterances

**Cause:** LLM over-segmented the conversation

**Solutions:**
```python
# Tune prompt temperature
loader = PromptLoader()
prompt_config = loader.get_prompt("initial_clustering")
prompt_config["temperature"] = 0.3  # Lower = more conservative

# Or post-process to merge small nodes
nodes = graph["nodes"]
merged_nodes = []
for i, node in enumerate(nodes):
    if len(node["utterance_ids"]) < 2:
        # Merge with next node
        if i + 1 < len(nodes):
            nodes[i + 1]["utterance_ids"].extend(node["utterance_ids"])
    else:
        merged_nodes.append(node)
```

### Issue: High cost / slow generation

**Symptoms:** Taking >60s or costing >$1 for small conversation

**Causes:**
- Using GPT-4 for large transcript
- Detecting contextual relationships

**Solutions:**
```python
# Use cheaper model for initial clustering
graph = await service.generate_graph(
    conversation_id=conv_id,
    transcript=transcript,
    model="gpt-3.5-turbo",  # 60x cheaper than GPT-4
)

# Skip relationship detection
graph = await service.generate_graph(
    conversation_id=conv_id,
    transcript=transcript,
    detect_relationships=False,
)

# Or use fallback entirely
service = GraphGenerationService(llm_client=None, db=db)
graph = await service.generate_graph(conv_id, transcript)
```

### Issue: Nodes have incorrect speakers

**Symptoms:** `primary_speaker` is wrong

**Cause:** LLM misidentified speakers or parsing error

**Solutions:**
```python
# Verify transcript has correct speakers
for utt in transcript.utterances:
    print(f"{utt.speaker}: {utt.text[:50]}")

# Manually correct node if needed
node = graph["nodes"][0]
node["speaker_info"]["primary_speaker"] = "Alice"

# Save corrected graph
await db.update_node(node["id"], node)
```

---

## Testing

Run the test suite:

```bash
pytest tests/test_graph_generation.py -v
```

**Test coverage:**
- 19 tests covering all functionality
- 100% pass rate
- Tests include:
  - Prompt loading and rendering
  - Graph generation with/without LLM
  - Temporal edge creation
  - Contextual relationship detection
  - Zoom level distribution
  - Edge cases (empty transcripts, single utterances)

**Example test:**
```python
@pytest.mark.asyncio
async def test_generate_graph_without_llm():
    """Test graph generation in fallback mode."""
    service = GraphGenerationService(llm_client=None, db=None)
    transcript = create_sample_transcript()

    graph = await service.generate_graph(
        conversation_id="test-123",
        transcript=transcript,
        save_to_db=False,
    )

    assert graph["node_count"] > 0
    assert graph["edge_count"] >= 0
    assert len(graph["nodes"]) == graph["node_count"]
```

---

## Future Enhancements

- [ ] **Hierarchical clustering**: Create parent-child node relationships
- [ ] **Embedding-based similarity**: Use vector embeddings for better relationship detection
- [ ] **Multi-conversation graphs**: Link related conversations
- [ ] **Dynamic zoom levels**: Adjust visibility based on user interaction
- [ ] **Graph visualization export**: Generate D3.js or Cytoscape.js visualizations
- [ ] **Node editing**: Allow manual node adjustments via API
- [ ] **Cluster refinement**: Iteratively improve clusters based on user feedback
- [ ] **Alternative LLM providers**: Support Anthropic Claude, Cohere, etc.

---

## References

- [Week 4 Roadmap](../docs/ROADMAP.md#week-4-initial-graph-generation)
- [Database Schema](DATABASE_MIGRATIONS.md)
- [Prompts Configuration](prompts.json)
- [Service Source Code](services/graph_generation.py)
- [API Endpoints](graph_api.py)
- [Test Suite](tests/test_graph_generation.py)

---

## Appendix: Example Full Workflow

```python
"""
Complete workflow: Import transcript → Generate graph → Retrieve results
"""
import asyncio
from parsers import GoogleMeetParser
from services import GraphGenerationService
from database import Database
import openai

async def main():
    # 1. Parse transcript
    parser = GoogleMeetParser()
    transcript = parser.parse_file("meeting.pdf")

    # Validate
    validation = parser.validate_transcript(transcript)
    if not validation.is_valid:
        print("❌ Invalid transcript:", validation.errors)
        return

    print(f"✓ Parsed {len(transcript.utterances)} utterances")
    print(f"  Participants: {', '.join(transcript.participants)}")
    print(f"  Duration: {transcript.duration}s")

    # 2. Save to database
    db = Database()
    conversation_id = await db.save_conversation(
        name="Product Planning Meeting",
        transcript=transcript,
    )
    print(f"✓ Saved conversation: {conversation_id}")

    # 3. Generate graph
    service = GraphGenerationService(llm_client=openai, db=db)

    print("Generating graph...")
    graph = await service.generate_graph(
        conversation_id=conversation_id,
        transcript=transcript,
        save_to_db=True,
    )

    print(f"✓ Generated graph:")
    print(f"  Nodes: {graph['node_count']}")
    print(f"  Edges: {graph['edge_count']}")
    print(f"  Zoom distribution: {graph['metadata']['zoom_level_distribution']}")

    # 4. Display results
    print("\n📊 Nodes:")
    for node in graph["nodes"][:5]:  # First 5 nodes
        print(f"\n  • {node['title']}")
        print(f"    {node['summary']}")
        print(f"    Zoom: {node['zoom_level_visible']}")
        print(f"    Speaker: {node['speaker_info']['primary_speaker']}")
        print(f"    Keywords: {', '.join(node['keywords'])}")

    print("\n🔗 Contextual Edges:")
    contextual = [e for e in graph["edges"] if e["relationship_type"] != "temporal"]
    for edge in contextual[:5]:  # First 5 contextual edges
        source = next(n for n in graph["nodes"] if n["id"] == edge["source_node_id"])
        target = next(n for n in graph["nodes"] if n["id"] == edge["target_node_id"])
        print(f"\n  {source['title']} → {target['title']}")
        print(f"    Type: {edge['relationship_type']}")
        print(f"    Strength: {edge['strength']:.2f}")
        if edge.get("description"):
            print(f"    {edge['description']}")

    print("\n✓ Workflow complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**
```
✓ Parsed 47 utterances
  Participants: Alice, Bob, Charlie, Diana
  Duration: 1847.5s
✓ Saved conversation: 550e8400-e29b-41d4-a716-446655440000
Generating graph...
✓ Generated graph:
  Nodes: 12
  Edges: 15
  Zoom distribution: {1: 2, 2: 3, 3: 4, 4: 2, 5: 1}

📊 Nodes:

  • Opening and Introductions
    Team greets each other and Alice opens the meeting
    Zoom: [3, 4, 5]
    Speaker: Alice
    Keywords: greeting, introduction, meeting start

  • Product Timeline Discussion
    Discussion of Q1 launch timeline and key milestones
    Zoom: [2, 3, 4]
    Speaker: Bob
    Keywords: timeline, Q1, launch, milestones

🔗 Contextual Edges:

  Product Timeline Discussion → Budget Allocation
    Type: theme
    Strength: 0.85
    Both nodes discuss resource planning

✓ Workflow complete!
```
