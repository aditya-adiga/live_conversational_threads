# Implicit Frame Detection

**Week 13 Implementation**
**Status**: ✅ Complete

## Overview

The Implicit Frame Detection system identifies underlying worldviews, assumptions, and interpretive frameworks that shape how participants understand and discuss topics in conversations. Unlike bias detection (Week 12), which finds systematic errors in reasoning, frame detection reveals the normative lenses through which reality is interpreted.

### Key Features

- **36+ Frame Types**: Comprehensive taxonomy across 6 categories
- **AI-Powered Detection**: Uses Claude 3.5 Sonnet with specialized prompts
- **Strength & Confidence Scoring**: Each detection includes 0-1 metrics
- **Assumptions Extraction**: What must be true for this frame to make sense
- **Implications Analysis**: What the frame reveals about underlying worldview
- **Category Distribution**: Visualize frame patterns across dimensions
- **Evidence Extraction**: See specific quotes exemplifying each frame
- **Interactive Filtering**: Focus on specific categories or frame types
- **Multi-Frame Nodes**: Detect multiple frames per node (e.g., economic + moral)

## Frame vs Bias: What's the Difference?

**Bias** (Week 12): Systematic errors in reasoning and judgment
- Example: Confirmation bias, anchoring, groupthink
- Focus: Flawed reasoning processes
- Goal: Identify cognitive errors

**Frame** (Week 13): Underlying worldviews and assumptions
- Example: Market fundamentalism, utilitarian ethics, long-term thinking
- Focus: Interpretive lenses
- Goal: Understand worldview diversity

**A node can have both**: "Everyone agrees the market will self-correct" exhibits both bandwagon effect (bias) AND market fundamentalism (frame).

## Frame Taxonomy

### 6 Categories, 36+ Frame Types

#### 1. Economic Frames
*Assumptions about markets, value, and resource allocation*

- **Market Fundamentalism**: Markets are the best way to organize society
- **Socialist Framework**: Collective ownership and equitable distribution
- **Growth Imperative**: Continuous economic growth is necessary
- **Scarcity Mindset**: Resources are fundamentally limited
- **Abundance Mindset**: There is enough for everyone
- **Zero-Sum Thinking**: One person's gain is another's loss

#### 2. Moral/Ethical Frames
*Underlying ethical principles and values*

- **Utilitarian**: Maximizing overall good and happiness
- **Deontological**: Focus on duties and moral rules
- **Virtue Ethics**: Character and virtues matter most
- **Care Ethics**: Relationships and empathy
- **Rights-Based**: Individual rights and freedoms
- **Consequentialist**: Judging actions by their outcomes

#### 3. Political Frames
*Assumptions about power and governance*

- **Progressive**: Social progress and reducing inequality
- **Conservative**: Tradition, stability, and gradual change
- **Libertarian**: Individual liberty and minimal government
- **Authoritarian**: Strong central authority
- **Egalitarian**: Equality and equal treatment
- **Meritocratic**: Success based on individual merit

#### 4. Scientific/Epistemological Frames
*How we know and understand the world*

- **Reductionist**: Breaking systems into component parts
- **Holistic**: Understanding as integrated wholes
- **Empiricist**: Knowledge from observation and evidence
- **Rationalist**: Knowledge from reason and logic
- **Constructivist**: Knowledge is socially constructed
- **Deterministic**: Events are causally determined

#### 5. Cultural Frames
*Identity, community, and social relations*

- **Individualist**: Individual autonomy as priority
- **Collectivist**: Group harmony as priority
- **Hierarchical**: Acceptance of ranked social structures
- **Egalitarian**: Minimizing status differences
- **Universalist**: Universal principles apply to all
- **Particularist**: Context and circumstances matter

#### 6. Temporal Frames
*Time, change, and progress perspectives*

- **Short-Term Focus**: Immediate concerns take priority
- **Long-Term Thinking**: Future impacts matter most
- **Cyclical View**: Time as recurring patterns
- **Linear Progress**: Continuous forward progress
- **Status Quo Permanence**: Current conditions will persist
- **Radical Change**: Transformative disruption expected

## Architecture

### Backend Services

#### FrameDetector Service

```python
class FrameDetector:
    async def analyze_conversation(conversation_id, force_reanalysis=False):
        """Returns: total_nodes, nodes_with_frames, frame_count,
                   by_category, by_frame, nodes"""

    async def _analyze_node(node, conversation_id):
        """Returns: List of detected frames with strength, confidence,
                    evidence, assumptions, implications"""

    async def get_conversation_results(conversation_id):
        """Get cached analysis results"""

    async def get_node_frames(node_id):
        """Get frames for specific node"""
```

**Key Features**:
- Multiple frames per node (e.g., economic + moral + temporal)
- Empty array for frame-neutral nodes (many factual nodes have zero frames)
- Strength: 0.0 (weak) to 1.0 (very strong) - how strongly the frame is present
- Confidence: 0.0 to 1.0 (only returns >0.6)
- **Assumptions**: Array of underlying beliefs required for this frame
- **Implications**: What this frame reveals about worldview (unique to frames)
- Evidence: Specific quotes exemplifying the frame

### Database Schema

#### FrameAnalysis Table

```sql
CREATE TABLE frame_analysis (
    id UUID PRIMARY KEY,
    node_id UUID REFERENCES nodes(id),
    conversation_id UUID REFERENCES conversations(id),
    frame_type TEXT NOT NULL,
    category TEXT NOT NULL,
    strength FLOAT CHECK (strength >= 0.0 AND strength <= 1.0),
    confidence FLOAT CHECK (confidence >= 0.0 AND confidence <= 1.0),
    description TEXT,
    evidence JSONB,
    assumptions JSONB,      -- NEW: Underlying assumptions
    implications TEXT,       -- NEW: Worldview implications
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_frame_node ON frame_analysis(node_id);
CREATE INDEX idx_frame_conversation ON frame_analysis(conversation_id);
CREATE INDEX idx_frame_type ON frame_analysis(frame_type);
CREATE INDEX idx_frame_category ON frame_analysis(category);
```

**Design**: One-to-many relationship (one node can have multiple frame analyses from different categories)

**Novel Fields**:
- `assumptions`: JSONB array of what must be believed for this frame
- `implications`: TEXT describing what this reveals about worldview

### Frontend Components

#### FrameAnalysis Page

**Route**: `/frames/:conversationId`

**Features**:
- Summary cards: Total nodes, nodes with frames, total frames, average per node
- Category distribution: 6 cards with color coding and click-to-filter
- Most common frames: Top 10 frame types with counts
- Node-by-node results: Detailed frame cards with evidence, assumptions, implications
- Dual filtering: By category AND by specific frame type
- Unique display: Shows assumptions and implications for deeper analysis

**Color Scheme**:
- Economic: Purple
- Moral: Blue
- Political: Green
- Scientific: Orange
- Cultural: Yellow
- Temporal: Red

## API Endpoints

### POST /api/conversations/{id}/frames/analyze

Analyze all nodes for implicit frames.

**Query Parameters**:
- `force_reanalysis` (boolean): Re-analyze even if results exist

**Response**:
```json
{
  "total_nodes": 50,
  "analyzed": 50,
  "nodes_with_frames": 22,
  "frame_count": 35,
  "by_category": {
    "economic": 12,
    "moral": 10,
    "political": 6,
    "temporal": 4,
    "scientific": 2,
    "cultural": 1
  },
  "by_frame": {
    "market_fundamentalism": 6,
    "utilitarian": 5,
    "long_term_thinking": 4
  },
  "nodes": [...]
}
```

### GET /api/conversations/{id}/frames

Get cached frame analysis results.

### GET /api/nodes/{id}/frames

Get frames for a specific node.

**Response**:
```json
{
  "frames": [
    {
      "frame_type": "market_fundamentalism",
      "category": "economic",
      "strength": 0.85,
      "confidence": 0.9,
      "description": "Strong belief in market-based solutions and self-regulation",
      "evidence": [
        "The market will naturally correct this inefficiency",
        "Competition drives optimal outcomes"
      ],
      "assumptions": [
        "Markets are efficient information processors",
        "Competition leads to optimal resource allocation",
        "Minimal regulation is preferable"
      ],
      "implications": "Reveals worldview favoring free-market capitalism, skepticism of government intervention, and belief in emergent market order",
      "analyzed_at": "2025-11-12T10:30:00Z"
    },
    {
      "frame_type": "long_term_thinking",
      "category": "temporal",
      "strength": 0.7,
      "confidence": 0.8,
      "description": "Emphasis on future impacts and long-term consequences",
      "evidence": [
        "We need to consider the impact on future generations"
      ],
      "assumptions": [
        "Future matters as much as present",
        "Long-term thinking leads to better decisions"
      ],
      "implications": "Suggests patience, sustainability focus, and willingness to accept short-term costs for long-term benefits",
      "analyzed_at": "2025-11-12T10:30:00Z"
    }
  ]
}
```

## Usage Workflow

### 1. Run Analysis

Navigate to `/frames/:conversationId` and click "Run Analysis".

Processing:
- Analyzes each node with Claude 3.5 Sonnet
- Returns 0-N frames per node (many factual nodes have zero)
- Multiple frames common (e.g., economic + moral + temporal)
- Only includes frames with confidence > 0.6
- ~2-4 seconds per node (slightly slower than bias detection due to complexity)

### 2. Review Distribution

**Category View**: See which frame types dominate the conversation
- High economic frames → discussion about markets, resources, efficiency
- High moral frames → ethical considerations, values-based reasoning
- High political frames → power dynamics, governance questions
- High temporal frames → focus on time horizons and change
- Balanced distribution → multi-dimensional discussion

**Top Frames View**: See most frequent specific frames
- Identifies dominant worldviews in the team
- Reveals what assumptions are taken for granted
- Shows potential for worldview conflicts

### 3. Examine Individual Nodes

Each detected frame shows:
- Frame name and category
- Strength level (Weak/Moderate/Strong/Very Strong)
- Confidence score
- Description of how it manifests
- **Evidence quotes** from the node
- **Underlying assumptions** (unique to frames!)
- **Worldview implications** (unique to frames!)

### 4. Filter and Focus

**By Category**: Click category card to see only those frames
**By Frame Type**: Click frame name to see all instances
**Combined**: Filter by both category and specific type

## Interpretation Guide

### Understanding Frame Diversity

**High Diversity** (many different frames):
- Participants approaching from different worldviews
- Rich, multi-dimensional discussion
- Potential for creative synthesis
- Also potential for misunderstanding if frames aren't explicit

**Low Diversity** (same frames repeated):
- Team shares worldview assumptions
- Communication may be easier
- Risk of groupthink
- May miss alternative perspectives

### Common Patterns

#### Startup Strategy Meeting

**Expected Frames**:
- Growth imperative (economic)
- Long-term thinking (temporal)
- Optimistic about disruption (radical change)
- Individualist/meritocratic (cultural/political)

**Interpretation**: Innovation-focused, growth-oriented worldview. May underweight stability and short-term concerns.

#### Government Policy Discussion

**Expected Frames**:
- Utilitarian or rights-based (moral)
- Progressive or conservative (political)
- Long-term thinking (temporal)
- Universalist (cultural)

**Interpretation**: Values-driven, policy-focused. Balance between progressive/conservative reveals ideological diversity.

#### Crisis Response

**Expected Frames**:
- Short-term focus (temporal)
- Consequentialist (moral)
- Deterministic (scientific)
- Hierarchical (cultural)

**Interpretation**: Urgency-driven, command-and-control. Natural for crisis but may miss long-term implications.

#### Academic/Research Discussion

**Expected Frames**:
- Empiricist or rationalist (scientific)
- Reductionist or holistic (scientific)
- Long-term thinking (temporal)
- Universalist (cultural)

**Interpretation**: Knowledge-focused, methodological. Balance between reductionist/holistic reveals epistemological diversity.

### Frame Conflicts

When participants operate from incompatible frames, misunderstanding occurs:

**Market Fundamentalism vs Socialist Framework**:
- Fundamental disagreement about resource allocation
- Requires acknowledging different starting assumptions
- Common in economic policy discussions

**Utilitarian vs Deontological**:
- "Ends justify means" vs "Principles matter regardless of outcomes"
- Classic moral philosophy tension
- Common in ethics discussions

**Short-Term vs Long-Term Thinking**:
- Immediate needs vs future sustainability
- Requires explicit trade-off discussion
- Common in strategy and planning

**Individualist vs Collectivist**:
- Personal autonomy vs group harmony
- Cultural dimension of disagreement
- Common in organizational culture discussions

## Testing

### Backend Tests

```bash
pytest tests/test_frame_detector.py -v
```

**Results**: 11 passed, 3 skipped

**Coverage**:
- ✅ Detector initialization
- ✅ Multi-frame detection
- ✅ Zero-frame handling (frame-neutral nodes)
- ✅ Error handling
- ✅ Empty conversation results
- ✅ Frame info utilities
- ✅ Category structure validation
- ✅ All frame types have metadata
- ✅ Assumptions and implications structure

## Performance

### Cost Analysis

**Per-Node**: ~$0.006-0.008
- Input: ~1200 tokens (prompt + node + 36 frame descriptions)
- Output: ~500 tokens (JSON with multiple frames + assumptions + implications)
- Slightly higher than bias detection due to more complex prompt

**Example Costs**:
- 25-node conversation: ~$0.15-0.20
- 100-node conversation: ~$0.60-0.80
- 500-node conversation: ~$3.00-4.00

**Optimization**: Results cached, no re-analysis unless forced.

### Processing Time

- Single node: ~2-4 seconds
- 50 nodes: ~3-5 minutes (concurrent processing)
- Results cached for instant re-display

## Integration Points

### Week 11: Simulacra Levels

Compare Simulacra levels with frame detection:
- Do Level 4 (Simulacrum) nodes have stronger ideological frames?
- Do Level 1 (Reality) nodes have fewer frames (more factual)?
- Relationship between abstraction and worldview expression

### Week 12: Cognitive Biases

Frames and biases interact:
- Confirmation bias + Market fundamentalism = Ignoring market failures
- Groupthink + Collectivist frame = Excessive conformity
- Authority bias + Hierarchical frame = Uncritical deference

### Week 8: Speaker Analytics

Cross-reference frames with speakers:
- Which speakers exhibit which frames?
- Do different roles (facilitator, expert) show different frames?
- Frame diversity across speaker distribution

### Decision Quality

Combine analyses for holistic view:
- High frame diversity + Low biases = Healthy multi-perspective discussion
- Low frame diversity + High confirmation bias = Echo chamber
- Economic frames only = Missing moral/social dimensions

## File Structure

```
lct_python_backend/
├── services/
│   └── frame_detector.py           # Detection service (700+ lines)
├── models.py                       # FrameAnalysis model
├── backend.py                      # API endpoints
├── prompts.json                    # frame_detection prompt
└── tests/
    └── test_frame_detector.py     # Unit tests

lct_app/src/
├── pages/
│   └── FrameAnalysis.jsx           # Main UI (500+ lines)
├── services/
│   └── frameApi.js                 # API client (220+ lines)
└── routes/
    └── AppRoutes.jsx               # Route config
```

## Example Analysis

### Example 1: Homogeneous Worldview (Low Diversity)

```json
{
  "nodes_with_frames": 28,
  "frame_count": 32,
  "by_category": {
    "economic": 20,
    "political": 8,
    "temporal": 4
  },
  "by_frame": {
    "market_fundamentalism": 15,
    "libertarian": 8,
    "short_term_focus": 4
  }
}
```

**Interpretation**: Strong free-market, libertarian worldview. Limited frame diversity. Risk: Missing other perspectives (moral, cultural). May not consider social impacts or long-term sustainability.

### Example 2: Rich Multi-Dimensional Discussion

```json
{
  "nodes_with_frames": 35,
  "frame_count": 58,
  "by_category": {
    "economic": 12,
    "moral": 15,
    "political": 10,
    "temporal": 9,
    "scientific": 8,
    "cultural": 4
  },
  "by_frame": {
    "utilitarian": 8,
    "long_term_thinking": 7,
    "market_fundamentalism": 5,
    "care_ethics": 4,
    "empiricist": 4
  }
}
```

**Interpretation**: High frame diversity across all categories. Multiple worldviews represented. Likely rich discussion with multiple perspectives. Potential for creative synthesis OR conflict if frames not explicitly discussed.

### Example 3: Frame Conflict Example

**Node A**: "We must maximize shareholder value and let the market decide."
- Frames: market_fundamentalism (economic), consequentialist (moral)

**Node B**: "We have a duty to our workers and community, not just shareholders."
- Frames: stakeholder_capitalism (economic), deontological (moral), care_ethics (moral)

**Analysis**: Fundamental frame conflict on both economic and moral dimensions. Requires acknowledging different starting assumptions for productive discussion.

## Troubleshooting

### High False Positives

**Symptom**: Many frames detected that don't seem accurate

**Solutions**:
- Check confidence scores (should be >0.6)
- Review evidence quotes and assumptions
- May indicate vague or metaphorical language in summaries
- Consider improving node summaries for clarity

### No Frames Detected

**Symptom**: Zero frames across all nodes

**Possibilities**:
- Genuinely factual, frame-neutral discussion (common for technical/procedural meetings!)
- Node summaries too generic or abstract
- Prompt may need domain-specific tuning
- Check backend logs for errors

### Too Many Frames Per Node

**Symptom**: 5+ frames per node

**Interpretation**:
- May be legitimate (rich, multi-dimensional content)
- Or may indicate overly interpretive analysis
- Check strength scores (many weak frames → less meaningful)
- Consider raising confidence threshold

## Future Enhancements

### Planned Features

1. **Frame Evolution**: Track how frames change over conversation time
2. **Speaker Frame Profiling**: Identify each speaker's characteristic frames
3. **Frame Conflict Detection**: Automatically identify incompatible frame pairs
4. **Consensus vs Diversity Metrics**: Quantify frame alignment
5. **Custom Frame Types**: Allow users to define domain-specific frames
6. **Frame-Aware Summarization**: Summaries that acknowledge multiple worldviews

### Research Directions

1. **Frame Correlations**: Which frames co-occur? (e.g., market fundamentalism + consequentialism)
2. **Decision Outcomes**: Do certain frame combinations predict better/worse outcomes?
3. **Conflict Resolution**: How can frame conflicts be productively managed?
4. **Cultural Patterns**: Frame distributions across cultures and domains
5. **Persuasion Dynamics**: How do frames spread through conversations?

## Relationship to Other Week 13 Features

Week 13 focuses on deeper AI analysis capabilities:

1. **Frame Detection** (this document): Worldview and assumption analysis
2. **Future Feature**: Argument mapping and reasoning chains
3. **Future Feature**: Counterfactual reasoning detection
4. **Future Feature**: Implicit vs explicit distinction

These features work together to provide comprehensive discourse analysis beyond surface content.

## Conclusion

Week 13's Implicit Frame Detection provides:

1. **Worldview Awareness**: Understand the lenses through which participants see reality
2. **Assumption Surfacing**: Make implicit beliefs explicit
3. **Diversity Assessment**: Measure frame diversity in discussions
4. **Conflict Understanding**: Identify root sources of disagreement
5. **Better Communication**: Enable frame-aware dialogue

The system is production-ready with comprehensive testing and documentation. It complements Week 12's bias detection by focusing on worldviews rather than reasoning errors.

---

**Implementation Date**: November 12, 2025
**Status**: ✅ Complete
**Lines of Code**: ~2,100 (backend + frontend + tests)
**Test Coverage**: 11 tests passing, 3 skipped
**Model**: Claude 3.5 Sonnet
**Cost**: ~$0.006-0.008 per node
