# Tier 2 Features - Advanced Analysis & Visualization

**Status**: Design Phase
**Date**: 2025-11-11
**Dependencies**: Tier 1 features must be implemented first

---

## Overview

Tier 2 features add advanced analytical capabilities on top of the core conversation graph. These features are designed to be **toggleable** by power users and **hidden by default** for casual users.

**Design principles**:
- AI works in background, not as "Clippy" in foreground
- Direct graph manipulation, not chat-based interaction
- All features generate training data from user corrections
- Cost tracking and performance metrics for all AI calls

---

## Feature 1: Node Detail Panel

### Architecture

**Layout**: Split screen
```
┌──────────────────────┬─────────────────────┐
│                      │                     │
│   CONTEXTUAL VIEW    │  NODE DETAIL PANEL  │
│   (Semantic network) │                     │
│                      │  📝 Transcript      │
│                      │  ─────────────────  │
├──────────────────────┤  🔗 Edges (mini-gr) │
│ TIMELINE (strip)     │  ─────────────────  │
│ [N1]→[N2]→[N3]→[N4]  │  ✅ Claims          │
│                      │  ─────────────────  │
└──────────────────────┤  ⚠️  Issues         │
                       └─────────────────────┘
```

### Context Display Logic (Zoom-Dependent)

```typescript
interface ContextConfig {
  zoom_level: number;  // 0.0 - 1.0
  mode: 'detailed' | 'focused' | 'summary';
  previous_nodes?: number;
  next_nodes?: number;
  summary_of?: 'entire_thread_arc';
}

function getContextConfig(zoom: number): ContextConfig {
  if (zoom >= 0.8) {
    // EXTREME ZOOM IN: Sentence/word level
    return {
      zoom_level: zoom,
      mode: 'detailed',
      previous_nodes: 2,
      next_nodes: 2
    };
  } else if (zoom < 0.3) {
    // EXTREME ZOOM OUT: Narrative arcs
    return {
      zoom_level: zoom,
      mode: 'summary',
      summary_of: 'entire_thread_arc'
    };
  } else {
    // MEDIUM: Topic level
    return {
      zoom_level: zoom,
      mode: 'focused',
      previous_nodes: 1,
      next_nodes: 1
    };
  }
}
```

### Sections

#### 1. Transcript & Context (Always Visible)

**Display**:
```
┌─────────────────────────────┐
│ 📝 Transcript               │
│                             │
│ [Previous context - gray]   │
│ Speaker A: ...              │
│                             │
│ [Current node - black]      │
│ Speaker B: This is the main │
│ content of the selected node│
│                             │
│ [Next context - gray]       │
│ Speaker A: ...              │
└─────────────────────────────┘
```

**Implementation**:
- Fetch `utterance_ids` from node
- Query `utterances` table for text
- Add context nodes based on zoom level
- Highlight speakers with consistent colors

#### 2. Edges & Dependencies (Collapsible)

**Display**: Mini-graph visualization
```
┌─────────────────────────────┐
│ 🔗 Edges & Dependencies ▼   │
│                             │
│      [Node 2]               │
│         ↓ (temporal: next)  │
│   → [THIS NODE] ←           │
│         ↓ (supports)        │
│      [Node 5]               │
│                             │
│  Legend:                    │
│  ─→ Temporal                │
│  ─→ Contextual (supports)   │
│  ─→ Contextual (contradicts)│
└─────────────────────────────┘
```

**Implementation**:
- Use D3.js or Cytoscape.js for mini-graph
- Show only 1-hop neighbors (directly connected nodes)
- Color-code edges by type
- Click edge → open edge editor (if in Edit Mode)

#### 3. Factual Claims (Collapsible)

**Display**:
```
┌─────────────────────────────┐
│ ✅ Factual Claims (3) ▼     │
│                             │
│ 1. "SK comes on 6th"        │
│    Source: Line 12          │
│    Confidence: 95%          │
│    [Fact-check this]        │
│                             │
│ 2. "ASF camp deadline is    │
│     in 10 days"             │
│    Source: Line 18          │
│    Confidence: 88%          │
│    [Fact-check this]        │
└─────────────────────────────┘
```

**Backend API**:
```python
@app.post("/api/extract-claims/{node_id}")
async def extract_claims(node_id: str):
    node = await db.get_node(node_id)
    utterances = await db.get_utterances(node.utterance_ids)

    prompt = load_prompt("extract_claims")  # From prompts.json
    response = await call_llm(prompt, {
        "utterances": [u.text for u in utterances],
        "context": await get_node_context(node_id)
    })

    # Log cost and time
    await log_api_call({
        "endpoint": "extract_claims",
        "model": response.model,
        "tokens": response.usage.total_tokens,
        "cost_usd": calculate_cost(response),
        "latency_ms": response.latency
    })

    return response.claims
```

**Future: On-Demand Fact-Checking**:
```python
@app.post("/api/fact-check-claim")
async def fact_check_claim(claim_text: str):
    # Use Perplexity API or Google Fact Check
    result = await perplexity.search(claim_text)
    return {
        "claim": claim_text,
        "verdict": "verified" | "contradictory" | "unable_to_verify",
        "confidence": 0.85,
        "sources": [{"url": "...", "snippet": "..."}]
    }
```

#### 4. Structural Issues (Collapsible, On-Demand)

**Display**:
```
┌─────────────────────────────┐
│ ⚠️  Structural Issues (2)▼  │
│                             │
│ 🔴 Strawman fallacy         │
│    Line 3: "So you're saying│
│    we should just give up?" │
│    → Speaker B misrepresents│
│    Speaker A's argument     │
│    [Not a fallacy] [Edit]   │
│                             │
│ 🟡 Weasel word              │
│    Line 5: "Some people..."│
│    → Vague attribution      │
│    [Dismiss] [Add note]     │
└─────────────────────────────┘
```

**Backend API** (lazy loading):
```python
@app.post("/api/detect-fallacies/{node_id}")
async def detect_fallacies(node_id: str):
    """
    Only called when user clicks node for the first time
    or clicks 'Refresh analysis'
    """
    node = await db.get_node(node_id)
    utterances = await db.get_utterances(node.utterance_ids)

    prompt = load_prompt("detect_fallacies")
    response = await call_llm(prompt, {
        "utterances": [u.text for u in utterances],
        "speakers": [u.speaker_name for u in utterances],
        "context": await get_node_context(node_id)
    })

    # Cache results
    await db.cache_analysis(node_id, "fallacies", response.issues)

    return {
        "severity": response.severity,  # none|low|medium|high
        "issues": response.issues
    }
```

**User Feedback (Training Data)**:
```python
@app.post("/api/feedback/fallacy")
async def feedback_on_fallacy(
    node_id: str,
    issue_id: str,
    action: "dismiss" | "confirm" | "edit",
    user_note: Optional[str] = None
):
    await db.log_edit({
        "edit_type": "fallacy_feedback",
        "node_id": node_id,
        "before": {"issue": await db.get_issue(issue_id)},
        "after": {"action": action, "user_note": user_note},
        "timestamp": datetime.now()
    })

    # If dismissed, reduce confidence for similar patterns
    if action == "dismiss":
        await update_fallacy_confidence(issue_id, decrement=0.1)
```

---

## Feature 2: Speaker Analytics View

### Navigation

**Separate view** (not sidebar) - switch via top nav:
```
[📊 Graph View] [📈 Analytics View] [⚙️  Settings]
```

### Layout

```
┌─────────────────────────────────────────────────┐
│             SPEAKER ANALYTICS                   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────────────────────────────────────┐   │
│ │  Speaker Breakdown                       │   │
│ │                                          │   │
│ │  Aditya ~     ████████████░░  45% (18m)  │   │
│ │  Sahil ~      ████████████████ 55% (22m) │   │
│ │  Harshit ~    ██░░░░░░░░░░░░░   8% (3m)  │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ ┌──────────────────────────────────────────┐   │
│ │  Turn Analysis                           │   │
│ │                                          │   │
│ │  Aditya:    47 turns │ Avg: 23s/turn    │   │
│ │  Sahil:     53 turns │ Avg: 25s/turn    │   │
│ │  Harshit:   12 turns │ Avg: 15s/turn    │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ ┌──────────────────────────────────────────┐   │
│ │  Topic Contributions                     │   │
│ │                                          │   │
│ │  Aditya:    #residency #guests #budgets  │   │
│ │  Sahil:     #vision #live-theory #events │   │
│ │  Harshit:   #logistics #communication    │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ ┌──────────────────────────────────────────┐   │
│ │  Conversational Roles                    │   │
│ │                                          │   │
│ │  Aditya:    🔨 Grounding (asks Q's)      │   │
│ │  Sahil:     🏗️  Constructing (proposes)  │   │
│ │  Harshit:   🎯 Facilitating (summarizes) │   │
│ └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Backend API

```python
@app.get("/api/analytics/speakers/{conversation_id}")
async def get_speaker_analytics(conversation_id: str):
    utterances = await db.get_all_utterances(conversation_id)
    nodes = await db.get_all_nodes(conversation_id)

    # Calculate speaking time from timestamps
    speaking_times = calculate_speaking_times(utterances)

    # Extract topics from nodes each speaker appears in
    topic_tags = await extract_speaker_topics(nodes, utterances)

    # Infer conversational roles using AI
    roles = await infer_conversational_roles(utterances, nodes)

    return {
        "speakers": [
            {
                "name": "Aditya",
                "speaking_time_seconds": 1112,
                "percentage": 45,
                "turn_count": 47,
                "avg_turn_duration": 23.7,
                "topics": ["#residency", "#guests", "#budgets"],
                "role": {"primary": "grounding", "confidence": 0.82}
            },
            # ... other speakers
        ]
    }
```

**Speaking Time Calculation** (from timestamps):
```python
def calculate_speaking_times(utterances: List[Utterance]) -> Dict[str, float]:
    """
    Parse timestamps from transcript and calculate precise durations

    Example timestamps in transcript:
    00:10:47
    Sahil ~: I can do...
    Aditya ~: I'd like to...

    00:12:26
    Sahil ~: me.
    """
    speaker_times = defaultdict(float)

    for i, utt in enumerate(utterances):
        if i < len(utterances) - 1:
            duration = utterances[i+1].start_time - utt.start_time
            speaker_times[utt.speaker_name] += duration
        else:
            # Last utterance: estimate from text length
            duration = len(utt.text.split()) * 0.5  # ~0.5s per word
            speaker_times[utt.speaker_name] += duration

    return dict(speaker_times)
```

**Topic Tagging** (few-shot prompting):
```python
async def extract_speaker_topics(
    nodes: List[Node],
    utterances: List[Utterance]
) -> Dict[str, List[str]]:
    """
    Use node summaries + few-shot prompting to extract topic tags
    """

    # Get nodes where each speaker appears
    speaker_nodes = {}
    for node in nodes:
        for utt_id in node.utterance_ids:
            utt = await db.get_utterance(utt_id)
            if utt.speaker_name not in speaker_nodes:
                speaker_nodes[utt.speaker_name] = []
            speaker_nodes[utt.speaker_name].append(node.summary)

    # Few-shot prompt
    prompt = load_prompt("extract_speaker_topics")

    # Example few-shot cases:
    examples = [
        {
            "summaries": ["Discussing guest invites", "Budget planning"],
            "tags": ["#guests", "#budgets"]
        },
        {
            "summaries": ["Vision for live theory", "Event planning"],
            "tags": ["#vision", "#live-theory", "#events"]
        }
    ]

    results = {}
    for speaker, summaries in speaker_nodes.items():
        response = await call_llm(prompt, {
            "examples": examples,
            "summaries": summaries
        })
        results[speaker] = response.tags

    return results
```

**Conversational Role Inference**:
```python
async def infer_conversational_roles(
    utterances: List[Utterance],
    nodes: List[Node]
) -> Dict[str, Dict]:
    """
    Analyze conversational patterns to infer roles:
    - Grounding: Asks clarifying questions, requests details
    - Constructing: Proposes ideas, builds frameworks
    - Deconstructing: Challenges assumptions, points out flaws
    - Facilitating: Summarizes, time-keeps, agenda-setting
    """

    prompt = load_prompt("infer_roles")

    response = await call_llm(prompt, {
        "utterances": [
            {"speaker": u.speaker_name, "text": u.text}
            for u in utterances[:100]  # Sample first 100 utterances
        ],
        "node_summaries": [n.summary for n in nodes]
    })

    return response.roles  # {"Aditya": {"primary": "grounding", "confidence": 0.82}}
```

---

## Feature 3: Prompts Configuration System

### File Structure

```
/config/prompts.json
```

**Schema**:
```json
{
  "version": "1.0.0",
  "prompts": {
    "extract_claims": {
      "description": "Extract factual claims from conversation nodes",
      "template": "Analyze this conversation segment...\n\n{utterances}\n\nReturn JSON...",
      "model": "gpt-4",
      "temperature": 0.3,
      "max_tokens": 500,
      "few_shot_examples": [
        {
          "input": "SK comes on 6th and leaves by 12th",
          "output": {"type": "factual", "verifiable": true}
        }
      ]
    },
    "detect_fallacies": {
      "description": "Detect logical fallacies and rhetorical issues",
      "template": "Analyze for fallacies...\n\n{utterances}\n\nIdentify:\n1. Logical fallacies...",
      "model": "claude-sonnet-4",
      "temperature": 0.2,
      "max_tokens": 800
    },
    "cluster_nodes": {
      "description": "Group nodes into semantic clusters based on zoom level",
      "template": "You have {node_count} nodes. Viewport: {viewport_width}x{viewport_height}...",
      "model": "gpt-4",
      "temperature": 0.4,
      "max_tokens": 1000
    },
    "extract_speaker_topics": {
      "description": "Extract topic tags for speaker from node summaries",
      "template": "Given these summaries by {speaker}:\n{summaries}\n\nExtract 3-5 topic tags...",
      "model": "gpt-3.5-turbo",
      "temperature": 0.5,
      "max_tokens": 200,
      "few_shot_examples": [
        {
          "input": ["Discussing guest invites", "Budget planning"],
          "output": ["#guests", "#budgets"]
        }
      ]
    },
    "infer_roles": {
      "description": "Infer conversational roles from utterance patterns",
      "template": "Analyze these conversation patterns and identify who is:\n- Grounding (asking questions)\n- Constructing (proposing ideas)\n- Deconstructing (challenging)\n- Facilitating (summarizing)\n\nUtterances:\n{utterances}",
      "model": "gpt-4",
      "temperature": 0.3,
      "max_tokens": 600
    }
  }
}
```

### Settings UI

```
⚙️  Settings > Prompts

┌──────────────────────────────────────┐
│ Prompt: extract_claims               │
├──────────────────────────────────────┤
│ Description:                         │
│ Extract factual claims from nodes    │
│                                      │
│ Model: [GPT-4 ▼]                     │
│ Temperature: [0.3] (0.0 - 1.0)       │
│ Max tokens: [500]                    │
│                                      │
│ Template:                            │
│ ┌────────────────────────────────┐   │
│ │ Analyze this conversation...   │   │
│ │                                │   │
│ │ {utterances}                   │   │
│ │                                │   │
│ │ Return JSON with claims...     │   │
│ └────────────────────────────────┘   │
│                                      │
│ [Test Prompt] [Save] [Reset Default] │
└──────────────────────────────────────┘
```

### Loading Prompts (Backend)

```python
# utils/prompts.py
import json
from pathlib import Path

_PROMPTS_CACHE = None

def load_prompt(prompt_name: str) -> Dict:
    global _PROMPTS_CACHE

    if _PROMPTS_CACHE is None:
        prompts_path = Path("config/prompts.json")
        with open(prompts_path) as f:
            _PROMPTS_CACHE = json.load(f)

    return _PROMPTS_CACHE["prompts"][prompt_name]

def reload_prompts():
    """Call this after user edits prompts.json"""
    global _PROMPTS_CACHE
    _PROMPTS_CACHE = None

# Usage in API endpoints:
async def extract_claims(node_id: str):
    prompt_config = load_prompt("extract_claims")

    response = await call_llm(
        template=prompt_config["template"],
        variables={"utterances": ...},
        model=prompt_config["model"],
        temperature=prompt_config["temperature"],
        max_tokens=prompt_config["max_tokens"]
    )

    return response
```

---

## Feature 4: Instrumentation & Cost Tracking

### Database Schema

```sql
api_calls_log (
  id UUID PRIMARY KEY,
  conversation_id UUID FK,
  endpoint TEXT,  -- "extract_claims", "detect_fallacies", etc.
  model TEXT,  -- "gpt-4", "claude-sonnet-4", etc.
  tokens_used INT,
  cost_usd DECIMAL(10, 6),
  latency_ms INT,
  timestamp TIMESTAMP,
  success BOOLEAN,
  error_message TEXT NULL
)
```

### Tracking Middleware

```python
# middleware/instrumentation.py
from functools import wraps
import time
from datetime import datetime

def track_api_call(endpoint_name: str):
    """Decorator to track cost and performance of LLM calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                response = await func(*args, **kwargs)

                # Calculate cost
                cost_usd = calculate_cost(
                    model=response.model,
                    tokens=response.usage.total_tokens
                )

                # Log to database
                await db.log_api_call({
                    "conversation_id": kwargs.get("conversation_id"),
                    "endpoint": endpoint_name,
                    "model": response.model,
                    "tokens_used": response.usage.total_tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now(),
                    "success": True
                })

                return response

            except Exception as e:
                # Log failure
                await db.log_api_call({
                    "conversation_id": kwargs.get("conversation_id"),
                    "endpoint": endpoint_name,
                    "model": None,
                    "tokens_used": 0,
                    "cost_usd": 0,
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now(),
                    "success": False,
                    "error_message": str(e)
                })
                raise

        return wrapper
    return decorator

# Usage:
@track_api_call("extract_claims")
async def extract_claims(node_id: str, conversation_id: str):
    # ... API call logic
    return response
```

### Cost Calculation

```python
# utils/pricing.py
PRICING = {
    "gpt-4": {
        "input": 0.03 / 1000,  # $0.03 per 1K tokens
        "output": 0.06 / 1000
    },
    "gpt-3.5-turbo": {
        "input": 0.0015 / 1000,
        "output": 0.002 / 1000
    },
    "claude-sonnet-4": {
        "input": 0.003 / 1000,
        "output": 0.015 / 1000
    }
}

def calculate_cost(model: str, tokens: int) -> float:
    """
    Estimate cost (rough average of input/output)
    More precise: track prompt_tokens and completion_tokens separately
    """
    if model not in PRICING:
        return 0.0  # Unknown model

    avg_price = (PRICING[model]["input"] + PRICING[model]["output"]) / 2
    return tokens * avg_price
```

### Settings UI - Cost Dashboard

```
⚙️  Settings > Cost & Performance

┌──────────────────────────────────────────┐
│ 💰 Total Spend (Last 30 Days)            │
│                                          │
│     $12.45                               │
│     ▲ 15% from last month                │
│                                          │
├──────────────────────────────────────────┤
│ 📊 Breakdown by Feature                  │
│                                          │
│  Clustering: ██████████░░  $4.20 (34%)   │
│  Claims:     ████████░░░░  $3.10 (25%)   │
│  Fallacies:  ███░░░░░░░░░  $1.85 (15%)   │
│  Roles:      ██░░░░░░░░░░  $1.30 (10%)   │
│  Other:      ████░░░░░░░░  $2.00 (16%)   │
│                                          │
├──────────────────────────────────────────┤
│ ⏱️  Average Latency                      │
│                                          │
│  Clustering:   1,240ms                   │
│  Claims:         680ms                   │
│  Fallacies:      920ms                   │
│  Roles:          510ms                   │
│                                          │
├──────────────────────────────────────────┤
│ ⚙️  Model Selection                      │
│                                          │
│  Primary model:   [GPT-4 ▼]              │
│  Fallback model:  [GPT-3.5-Turbo ▼]      │
│                                          │
│  [X] Auto-downgrade on error             │
│  [X] Warn if cost > $1/conversation      │
│                                          │
│  Credit limit:  [$50/month]              │
│  Current usage: $12.45 / $50.00          │
│                                          │
└──────────────────────────────────────────┘
```

---

## Feature 5: Edit History & Training Data

### JSON Schema (Detailed)

```typescript
interface EditLog {
  edit_id: string;  // UUID
  conversation_id: string;
  user_id: string;  // Future: for multi-user
  timestamp: string;  // ISO 8601
  edit_type:
    | "node_summary_edit"
    | "node_merge"
    | "node_split"
    | "edge_add"
    | "edge_remove"
    | "edge_relabel"
    | "fallacy_dismiss"
    | "fallacy_confirm"
    | "claim_edit"
    | "cluster_create"
    | "cluster_dissolve";

  context: {
    zoom_level: number;
    view_mode: "temporal" | "contextual";
    node_id?: string;
    edge_id?: string;
  };

  before: any;  // Type depends on edit_type
  after: any;

  user_note?: string;  // Optional for most edits, required for fallacy dismissal
}
```

**Example edit logs**:

```json
{
  "edit_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "conv_123",
  "user_id": "user_456",
  "timestamp": "2025-11-11T10:45:23Z",
  "edit_type": "node_summary_edit",
  "context": {
    "zoom_level": 0.75,
    "view_mode": "contextual",
    "node_id": "node_7"
  },
  "before": {
    "summary": "Discussion about guest invites"
  },
  "after": {
    "summary": "Decision to invite all 6 guests to residency"
  },
  "user_note": "AI summary was too vague - this was a decision, not just discussion"
}
```

```json
{
  "edit_id": "660e9500-f39c-52e5-b827-557766551111",
  "conversation_id": "conv_123",
  "user_id": "user_456",
  "timestamp": "2025-11-11T10:47:15Z",
  "edit_type": "fallacy_dismiss",
  "context": {
    "zoom_level": 0.50,
    "view_mode": "contextual",
    "node_id": "node_12"
  },
  "before": {
    "issue_type": "strawman",
    "text": "So you're saying we should just give up?",
    "ai_confidence": 0.75
  },
  "after": {
    "dismissed": true,
    "reason": "not_a_fallacy"
  },
  "user_note": "This was rhetorical, not an actual misrepresentation. Context matters."
}
```

### Training Data Export

```python
@app.get("/api/export/training-data")
async def export_training_data(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Export all edit logs as training data for model fine-tuning
    """
    edits = await db.get_all_edits(start_date, end_date)

    # Format for fine-tuning
    training_examples = []
    for edit in edits:
        if edit.edit_type == "node_summary_edit":
            training_examples.append({
                "prompt": f"Summarize: {edit.before['summary']}",
                "completion": edit.after['summary'],
                "metadata": {
                    "user_note": edit.user_note,
                    "zoom_level": edit.context['zoom_level']
                }
            })
        elif edit.edit_type == "fallacy_dismiss":
            training_examples.append({
                "prompt": f"Is this a {edit.before['issue_type']}? {edit.before['text']}",
                "completion": "No, this is not a fallacy.",
                "reason": edit.user_note
            })

    return {
        "version": "1.0.0",
        "export_date": datetime.now().isoformat(),
        "count": len(training_examples),
        "examples": training_examples
    }
```

### Edit History UI (Collapsible in Settings)

```
⚙️  Settings > Edit History

┌──────────────────────────────────────────┐
│ 📝 Recent Edits                          │
│                                          │
│ Node 7 - Nov 11, 10:45 ▼                 │
│ ├─ Changed summary                       │
│ │  Before: "Discussion about guests"     │
│ │  After: "Decision to invite all 6"     │
│ │  Note: "AI was too vague"              │
│ │  [Revert] [View node]                  │
│                                          │
│ Node 12 - Nov 11, 10:47 ▼                │
│ ├─ Dismissed fallacy detection           │
│ │  Type: strawman                        │
│ │  Note: "Rhetorical, not misrepresent"  │
│ │  [Restore flag] [View node]            │
│                                          │
│ Node 15 - Nov 11, 10:50 ▼                │
│ ├─ Added contextual edge                 │
│ │  From: Node 15 → Node 8                │
│ │  Type: supports                        │
│ │  Note: "Supports budget discussion"    │
│ │  [Remove edge] [View node]             │
│                                          │
│ [Export Training Data] [Clear Old Edits] │
└──────────────────────────────────────────┘
```

---

## Feature 6: Power User Settings

### Toggleable Features

```
⚙️  Settings > Features

┌──────────────────────────────────────────┐
│ 🎛️  Feature Toggles                      │
│                                          │
│ [✓] Show fallacy detection               │
│     └─ [✓] Auto-run on node click        │
│     └─ [ ] Require manual trigger        │
│                                          │
│ [✓] Show claim extraction                │
│     └─ [✓] Extract on import             │
│     └─ [ ] Extract on-demand only        │
│                                          │
│ [✓] Show edit history                    │
│                                          │
│ [✓] Show speaker analytics               │
│                                          │
│ [✓] Show cost tracking                   │
│                                          │
│ [ ] Enable experimental features         │
│     └─ [ ] Simulacra level detection     │
│     └─ [ ] Auto fact-checking            │
│                                          │
│ ─────────────────────────────────────── │
│                                          │
│ 🎨 UI Preferences                        │
│                                          │
│ Complexity:  [○ Simple  ● Power User]    │
│              (Hides advanced features)   │
│                                          │
│ Default zoom: [50%]                      │
│ Default view: [◉ Contextual  ○ Timeline] │
│                                          │
└──────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Node Detail Panel (Week 6)
- [ ] Split screen layout
- [ ] Zoom-dependent context logic
- [ ] Collapsible sections
- [ ] Mini-graph for edges

### Phase 2: Claim Extraction & Fallacy Detection (Week 7)
- [ ] Claims extraction API
- [ ] Fallacy detection API (lazy loading)
- [ ] User feedback mechanism
- [ ] Training data logging

### Phase 3: Speaker Analytics (Week 8)
- [ ] Separate analytics view
- [ ] Speaking time calculation
- [ ] Topic tagging
- [ ] Role inference

### Phase 4: Infrastructure (Week 9)
- [ ] Prompts configuration system
- [ ] Instrumentation middleware
- [ ] Cost tracking dashboard
- [ ] Edit history UI

### Phase 5: Power User Features (Week 10)
- [ ] Feature toggles
- [ ] Training data export
- [ ] Settings UI
- [ ] Documentation

---

## Future Iterations

### Simulacra Level Detection
(Awaiting user context document)

- Detect implicit frames in language
- Identify normative claims masquerading as facts
- Example: "preserve light of consciousness" → hidden values

### Auto Fact-Checking
- Integrate Perplexity API
- On-demand only (user clicks button)
- Show sources and confidence

### Multi-User Collaboration
- Real-time collaborative editing
- Conflict resolution
- User permissions

---

**Status**: Ready for review and implementation planning
**Next Steps**: Review, prioritize phases, begin Phase 1 implementation
