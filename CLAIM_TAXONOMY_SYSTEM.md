# Three-Layer Claim Taxonomy System

## Overview

Extends existing frame detection to provide comprehensive claim analysis across three layers:
1. **Factual Claims**: Verifiable statements about reality
2. **Normative Claims**: Value judgments and "ought" statements
3. **Worldview Claims**: Implicit ideological frames and hidden premises

---

## Database Schema

### New Table: `claims`

```sql
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,

    -- Claim Content
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('factual', 'normative', 'worldview')),

    -- Source
    utterance_ids UUID[] NOT NULL,  -- Which utterances contain this claim
    speaker_name TEXT,

    -- Classification Confidence
    strength FLOAT NOT NULL CHECK (strength >= 0.0 AND strength <= 1.0),
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Factual Claims
    is_verifiable BOOLEAN,
    verification_status TEXT CHECK (verification_status IN ('verified', 'false', 'misleading', 'unverifiable', 'pending')),
    fact_check_result JSONB,  -- From Perplexity API
    fact_checked_at TIMESTAMP,

    -- Normative Claims
    normative_type TEXT CHECK (normative_type IN ('prescription', 'evaluation', 'obligation', 'preference')),
    implicit_values TEXT[],  -- Underlying values (e.g., 'growth', 'fairness', 'efficiency')

    -- Worldview Claims
    worldview_category TEXT,  -- From frame detection taxonomy
    hidden_premises TEXT[],  -- Unstated assumptions
    ideological_markers TEXT[],

    -- Relationships
    supports_claim_ids UUID[],  -- Claims this supports
    contradicts_claim_ids UUID[],  -- Claims this contradicts
    depends_on_claim_ids UUID[],  -- Premises this depends on

    -- Metadata
    analyzed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_claims_conversation (conversation_id),
    INDEX idx_claims_node (node_id),
    INDEX idx_claims_type (claim_type),
    INDEX idx_claims_speaker (conversation_id, speaker_name)
);
```

### New Table: `is_ought_conflations`

```sql
CREATE TABLE is_ought_conflations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,

    -- The Conflation
    descriptive_claim_id UUID REFERENCES claims(id),  -- "Is" statement
    normative_claim_id UUID REFERENCES claims(id),    -- "Ought" statement

    -- Analysis
    conflation_text TEXT NOT NULL,  -- Full text containing the conflation
    explanation TEXT NOT NULL,      -- Why this is problematic
    fallacy_type TEXT CHECK (fallacy_type IN ('naturalistic_fallacy', 'appeal_to_nature', 'appeal_to_tradition', 'appeal_to_popularity')),

    -- Evidence
    utterance_ids UUID[] NOT NULL,
    speaker_name TEXT,

    -- Confidence
    strength FLOAT NOT NULL CHECK (strength >= 0.0 AND strength <= 1.0),
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Metadata
    detected_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_conflations_conversation (conversation_id),
    INDEX idx_conflations_node (node_id)
);
```

### New Table: `argument_trees`

```sql
CREATE TABLE argument_trees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Tree Structure
    root_claim_id UUID NOT NULL REFERENCES claims(id),  -- Main conclusion
    tree_structure JSONB NOT NULL,  -- Full tree as nested JSON

    -- Metadata
    title TEXT,
    summary TEXT,

    -- Analysis
    argument_type TEXT CHECK (argument_type IN ('deductive', 'inductive', 'abductive')),
    is_valid BOOLEAN,  -- Logically valid structure?
    is_sound BOOLEAN,  -- Valid + true premises?
    identified_fallacies TEXT[],
    circular_dependencies UUID[],  -- Claim IDs that form circular reasoning

    -- Display
    visualization_data JSONB,  -- For rendering tree UI

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_argument_trees_conversation (conversation_id),
    INDEX idx_argument_trees_root (root_claim_id)
);
```

### New Table: `double_crux_analysis`

```sql
CREATE TABLE double_crux_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Participants
    speaker_a TEXT NOT NULL,
    speaker_b TEXT NOT NULL,

    -- Disagreement
    disagreement_summary TEXT NOT NULL,
    topic TEXT,

    -- Cruxes (Key disagreement points)
    cruxes JSONB NOT NULL,  -- Array of {claim_id, speaker, crux_text, would_change_mind}

    -- Underlying Assumptions
    speaker_a_assumptions UUID[],  -- Claim IDs
    speaker_b_assumptions UUID[],

    -- Shared Ground
    shared_assumptions UUID[],
    points_of_agreement TEXT[],

    -- Analysis
    crux_depth INTEGER,  -- How deep did we dig? (1-5)
    resolution_path TEXT,  -- Suggested path to agreement

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_double_crux_conversation (conversation_id),
    INDEX idx_double_crux_speakers (conversation_id, speaker_a, speaker_b)
);
```

---

## Service Architecture

### 1. Claim Detection Service

```python
# lct_python_backend/services/claim_detector.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import anthropic
import os

class ClaimDetector:
    """
    Three-layer claim detection service.

    Detects:
    1. Factual claims (verifiable)
    2. Normative claims (value judgments)
    3. Worldview claims (implicit ideology)
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.prompt_manager = get_prompt_manager()

    async def analyze_conversation(
        self,
        conversation_id: str,
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze all nodes in conversation for claims.

        Returns:
            {
                "total_claims": 45,
                "by_type": {
                    "factual": 20,
                    "normative": 15,
                    "worldview": 10
                },
                "by_speaker": {...},
                "claims": [...]
            }
        """
        # Get all nodes
        nodes = await self._get_conversation_nodes(conversation_id)

        all_claims = []

        for node in nodes:
            # Check if already analyzed
            if not force_reanalysis:
                existing = await self._get_node_claims(node.id)
                if existing:
                    all_claims.extend(existing)
                    continue

            # Analyze node for claims
            claims = await self._detect_claims_in_node(conversation_id, node)
            all_claims.extend(claims)

        # Aggregate results
        return self._aggregate_results(all_claims)

    async def _detect_claims_in_node(
        self,
        conversation_id: str,
        node: Node
    ) -> List[Dict[str, Any]]:
        """
        Detect all three types of claims in a single node.
        """
        # Get utterances
        utterances = await self._get_node_utterances(node)

        # Render prompt
        prompt = self.prompt_manager.render_prompt(
            "detect_claims_three_layer",
            {
                "node_title": node.title,
                "node_summary": node.summary,
                "utterances": self._format_utterances(utterances),
            }
        )

        # Call Claude
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        claims_data = self._parse_claims_response(response)

        # Save to database
        saved_claims = []
        for claim_data in claims_data:
            claim = await self._save_claim(conversation_id, node.id, claim_data, utterances)
            saved_claims.append(claim)

        return saved_claims

    def _parse_claims_response(self, response) -> List[Dict]:
        """Parse Claude's response into structured claims."""
        import json

        content = response.content[0].text

        # Extract JSON (handle markdown blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()

        try:
            data = json.loads(content)
            return data.get("claims", [])
        except json.JSONDecodeError:
            return []

    async def _save_claim(
        self,
        conversation_id: str,
        node_id: str,
        claim_data: Dict,
        utterances: List
    ) -> Dict:
        """Save claim to database and return dict representation."""
        from models import Claim
        import uuid

        # Map utterance indices to IDs
        utterance_ids = [
            utterances[idx].id
            for idx in claim_data.get("utterance_indices", [])
            if idx < len(utterances)
        ]

        claim = Claim(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            node_id=uuid.UUID(node_id),
            claim_text=claim_data["claim_text"],
            claim_type=claim_data["claim_type"],
            utterance_ids=[uuid.UUID(str(uid)) for uid in utterance_ids],
            speaker_name=claim_data.get("speaker"),
            strength=claim_data.get("strength", 0.7),
            confidence=claim_data.get("confidence", 0.7),
            is_verifiable=claim_data.get("is_verifiable"),
            normative_type=claim_data.get("normative_type"),
            implicit_values=claim_data.get("implicit_values", []),
            worldview_category=claim_data.get("worldview_category"),
            hidden_premises=claim_data.get("hidden_premises", []),
            ideological_markers=claim_data.get("ideological_markers", []),
        )

        self.db.add(claim)
        await self.db.commit()
        await self.db.refresh(claim)

        return self._claim_to_dict(claim)

    def _format_utterances(self, utterances: List) -> str:
        """Format utterances for prompt."""
        lines = []
        for i, utt in enumerate(utterances):
            lines.append(f"[{i}] {utt.speaker_name}: {utt.text}")
        return "\n".join(lines)

    def _claim_to_dict(self, claim) -> Dict:
        """Convert Claim model to dict."""
        return {
            "id": str(claim.id),
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "speaker": claim.speaker_name,
            "strength": claim.strength,
            "confidence": claim.confidence,
            "is_verifiable": claim.is_verifiable,
            "normative_type": claim.normative_type,
            "implicit_values": claim.implicit_values,
            "worldview_category": claim.worldview_category,
            "hidden_premises": claim.hidden_premises,
        }
```

---

## Prompts Configuration

### `prompts.json` - New Entry

```json
{
  "detect_claims_three_layer": {
    "description": "Detect factual, normative, and worldview claims in conversation nodes",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.3,
    "max_tokens": 4000,
    "template": "You are analyzing a conversation segment to identify three types of claims:\n\n1. FACTUAL CLAIMS: Verifiable statements about reality\n   - Example: \"The meeting is on Tuesday\"\n   - Example: \"GDP grew 3% last quarter\"\n\n2. NORMATIVE CLAIMS: Value judgments, prescriptions, \"ought\" statements\n   - Example: \"We should prioritize user experience\"\n   - Example: \"Economic growth is more important than equality\"\n\n3. WORLDVIEW CLAIMS: Implicit ideological frames, hidden assumptions\n   - Example: \"Progress requires disruption\" (assumes: change = good, status quo = bad)\n   - Example: \"Natural selection optimizes\" (assumes: evolution has direction/goal)\n\n---\n\nNode Title: {node_title}\nNode Summary: {node_summary}\n\nUtterances:\n{utterances}\n\n---\n\nINSTRUCTIONS:\n\n1. Identify ALL claims of each type\n2. For factual claims: Note if verifiable (can we fact-check this?)\n3. For normative claims: Identify the implicit values (e.g., 'efficiency', 'fairness', 'freedom')\n4. For worldview claims: Unpack the hidden premises (what unstated beliefs does this require?)\n5. Assign strength (0-1): How central is this claim to the speaker's argument?\n6. Assign confidence (0-1): How confident are you in this classification?\n\nReturn JSON:\n```json\n{\n  \"claims\": [\n    {\n      \"claim_text\": \"The specific claim\",\n      \"claim_type\": \"factual\" | \"normative\" | \"worldview\",\n      \"speaker\": \"Speaker name\",\n      \"utterance_indices\": [0, 1],  // Which utterance(s) contain this\n      \"strength\": 0.8,\n      \"confidence\": 0.9,\n      \n      // For factual claims only:\n      \"is_verifiable\": true,\n      \n      // For normative claims only:\n      \"normative_type\": \"prescription\" | \"evaluation\" | \"obligation\" | \"preference\",\n      \"implicit_values\": [\"growth\", \"innovation\"],\n      \n      // For worldview claims only:\n      \"worldview_category\": \"economic_neoliberal\" | \"moral_utilitarian\" | etc,\n      \"hidden_premises\": [\"Markets are efficient\", \"Individuals are rational\"],\n      \"ideological_markers\": [\"invisible hand\", \"rational actor\"]\n    }\n  ]\n}\n```"
  }
}
```

---

## API Endpoints

### Backend Routes

```python
# lct_python_backend/backend.py

@lct_app.post("/api/conversations/{conversation_id}/claims/analyze")
async def analyze_claims(
    conversation_id: str,
    force_reanalysis: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze conversation for factual, normative, and worldview claims.

    Returns:
        {
            "total_claims": 45,
            "by_type": {"factual": 20, "normative": 15, "worldview": 10},
            "by_speaker": {...},
            "claims": [...]
        }
    """
    detector = ClaimDetector(db)
    results = await detector.analyze_conversation(conversation_id, force_reanalysis)
    return results


@lct_app.get("/api/conversations/{conversation_id}/claims")
async def get_claims(
    conversation_id: str,
    claim_type: Optional[str] = None,  # Filter by type
    speaker: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all claims for a conversation with optional filters."""
    query = select(Claim).where(Claim.conversation_id == uuid.UUID(conversation_id))

    if claim_type:
        query = query.where(Claim.claim_type == claim_type)
    if speaker:
        query = query.where(Claim.speaker_name == speaker)

    result = await db.execute(query)
    claims = result.scalars().all()

    return {
        "conversation_id": conversation_id,
        "count": len(claims),
        "claims": [claim_to_dict(c) for c in claims]
    }


@lct_app.get("/api/claims/{claim_id}")
async def get_claim_details(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific claim."""
    query = select(Claim).where(Claim.id == uuid.UUID(claim_id))
    result = await db.execute(query)
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get related claims (supports/contradicts)
    supports = []
    contradicts = []
    if claim.supports_claim_ids:
        supports_query = select(Claim).where(Claim.id.in_(claim.supports_claim_ids))
        supports = (await db.execute(supports_query)).scalars().all()

    if claim.contradicts_claim_ids:
        contradicts_query = select(Claim).where(Claim.id.in_(claim.contradicts_claim_ids))
        contradicts = (await db.execute(contradicts_query)).scalars().all()

    return {
        **claim_to_dict(claim),
        "supports": [claim_to_dict(c) for c in supports],
        "contradicts": [claim_to_dict(c) for c in contradicts],
    }
```

---

## Frontend UI

### Claim Analysis Page

```jsx
// lct_app/src/pages/ClaimAnalysis.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'router-dom';
import { analyzeThreeLayerClaims, getClaims } from '../services/claimApi';

export default function ClaimAnalysis() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [claims, setClaims] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [filterSpeaker, setFilterSpeaker] = useState('all');

  useEffect(() => {
    loadClaims();
  }, [conversationId]);

  const loadClaims = async () => {
    setLoading(true);
    try {
      // Check if already analyzed
      const existing = await getClaims(conversationId);

      if (existing.count === 0) {
        // Need to analyze first
        await analyzeThreeLayerClaims(conversationId);
        const analyzed = await getClaims(conversationId);
        setClaims(analyzed);
      } else {
        setClaims(existing);
      }
    } catch (error) {
      console.error('Error loading claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredClaims = claims?.claims.filter(claim => {
    if (filterType !== 'all' && claim.claim_type !== filterType) return false;
    if (filterSpeaker !== 'all' && claim.speaker !== filterSpeaker) return false;
    return true;
  }) || [];

  const speakers = [...new Set(claims?.claims.map(c => c.speaker) || [])];

  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="text-xl">Analyzing claims...</div>
    </div>;
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Three-Layer Claim Analysis</h1>
        <button
          onClick={() => navigate(`/conversation/${conversationId}`)}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          ← Back to Conversation
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-100 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-800">
            {claims?.by_type?.factual || 0}
          </div>
          <div className="text-blue-600">Factual Claims</div>
          <div className="text-sm text-blue-500">Verifiable statements</div>
        </div>

        <div className="bg-purple-100 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-800">
            {claims?.by_type?.normative || 0}
          </div>
          <div className="text-purple-600">Normative Claims</div>
          <div className="text-sm text-purple-500">Value judgments</div>
        </div>

        <div className="bg-green-100 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-800">
            {claims?.by_type?.worldview || 0}
          </div>
          <div className="text-green-600">Worldview Claims</div>
          <div className="text-sm text-green-500">Implicit ideology</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="all">All Types</option>
          <option value="factual">Factual</option>
          <option value="normative">Normative</option>
          <option value="worldview">Worldview</option>
        </select>

        <select
          value={filterSpeaker}
          onChange={(e) => setFilterSpeaker(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="all">All Speakers</option>
          {speakers.map(speaker => (
            <key={speaker} value={speaker}>{speaker}</option>
          ))}
        </select>
      </div>

      {/* Claims List */}
      <div className="space-y-4">
        {filteredClaims.map(claim => (
          <ClaimCard key={claim.id} claim={claim} />
        ))}
      </div>
    </div>
  );
}

function ClaimCard({ claim }) {
  const typeColors = {
    factual: 'border-blue-500 bg-blue-50',
    normative: 'border-purple-500 bg-purple-50',
    worldview: 'border-green-500 bg-green-50'
  };

  const typeIcons = {
    factual: '📊',
    normative: '⚖️',
    worldview: '🌍'
  };

  return (
    <div className={`border-l-4 p-4 rounded ${typeColors[claim.claim_type]}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{typeIcons[claim.claim_type]}</span>
            <span className="font-semibold text-gray-700 uppercase text-sm">
              {claim.claim_type}
            </span>
            <span className="text-gray-500">•</span>
            <span className="text-gray-600">{claim.speaker}</span>
          </div>

          <p className="text-lg mb-2">{claim.claim_text}</p>

          {/* Type-specific details */}
          {claim.claim_type === 'factual' && claim.is_verifiable && (
            <div className="text-sm text-blue-600">
              ✓ Verifiable claim
            </div>
          )}

          {claim.claim_type === 'normative' && claim.implicit_values?.length > 0 && (
            <div className="mt-2">
              <div className="text-sm font-semibold text-purple-700">Implicit Values:</div>
              <div className="flex flex-wrap gap-2 mt-1">
                {claim.implicit_values.map(value => (
                  <span key={value} className="px-2 py-1 bg-purple-200 text-purple-800 rounded text-sm">
                    {value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {claim.claim_type === 'worldview' && claim.hidden_premises?.length > 0 && (
            <div className="mt-2">
              <div className="text-sm font-semibold text-green-700">Hidden Premises:</div>
              <ul className="list-disc list-inside mt-1 text-sm text-green-600">
                {claim.hidden_premises.map((premise, idx) => (
                  <li key={idx}>{premise}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="text-right text-sm text-gray-500">
          <div>Strength: {(claim.strength * 100).toFixed(0)}%</div>
          <div>Confidence: {(claim.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>
    </div>
  );
}
```

---

## Testing Strategy

```python
# lct_python_backend/tests/test_claim_detector.py

import pytest
from services.claim_detector import ClaimDetector

@pytest.mark.asyncio
async def test_detect_factual_claim():
    """Test detection of verifiable factual claims"""
    # Mock conversation with clear factual claim
    # Assert claim_type == 'factual' and is_verifiable == True

@pytest.mark.asyncio
async def test_detect_normative_claim():
    """Test detection of value judgments"""
    # Mock conversation with "should" statement
    # Assert claim_type == 'normative' and implicit_values extracted

@pytest.mark.asyncio
async def test_detect_worldview_claim():
    """Test detection of implicit ideology"""
    # Mock conversation with ideological frame
    # Assert claim_type == 'worldview' and hidden_premises identified

@pytest.mark.asyncio
async def test_three_layer_integration():
    """Test that all three types detected in mixed conversation"""
    # Mock complex conversation
    # Assert all three types present
```

---

## Cost Estimation

**Per Conversation** (assuming 50 nodes):
- Claude API calls: 50 nodes × $0.015 per call = **$0.75**
- Average conversation analysis: **< $1.00**

**Development/Testing** (100 test conversations):
- **~$100**

---

## Success Metrics

1. **Detection Accuracy**: Manual validation on 50 conversations
   - Target: >80% for factual, >70% for normative, >60% for worldview

2. **User Feedback**: Track corrections via UI
   - Target: <20% correction rate

3. **Coverage**: % of nodes with at least one claim
   - Target: >80% of nodes

4. **Performance**: Analysis time per conversation
   - Target: <30 seconds for 50-node conversation

---

## Next Steps After Phase 1

Once three-layer taxonomy is working:
- **Phase 2**: Is-Ought Conflation Detection
- **Phase 3**: Argument Mapping
- **Phase 4**: Perplexity Integration
- **Phase 5**: Double Crux Analysis

Continue to next phase? I'll create detailed specs for each.
