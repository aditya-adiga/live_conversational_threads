# Advanced Passive Analysis & Cross-Conversation Search
## 6-Week Roadmap (Weeks 15-20)

**Last Updated**: 2025-11-12
**Philosophy**: Passive consumption, not active interference. Build infrastructure for understanding conversations AFTER they happen, and for searching/connecting ideas ACROSS conversations.

---

## Core Principles

1. **Passive, Not Parasitic**: Analysis happens in background, never interrupts
2. **Cross-Conversation Knowledge Graph**: Connect ideas across your entire conversation history
3. **Semantic Search**: Find ideas by meaning, not just keywords
4. **Entropy-Based Segmentation**: Find natural conversation boundaries where information density changes
5. **Consumption-Focused**: Help users UNDERSTAND conversations, not CONTROL them

---

## Phase 1: Advanced Claim Analysis (Weeks 15-16)

### Goal
Extract structured knowledge (claims, arguments) from conversations to enable cross-conversation search.

### Week 15: Three-Layer Claim Taxonomy

**Why This Matters for Cross-Conversation Search**:
- Extract factual claims → Search "What facts did I learn about X?"
- Extract normative claims → Search "What values do I express about Y?"
- Extract worldview claims → Search "What assumptions underlie my thinking on Z?"

**Implementation**:

#### 1. Database Schema (Claims as Search Units)

```sql
-- Claims become the atomic search unit across conversations
CREATE TABLE claims (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    node_id UUID NOT NULL,

    -- Content
    claim_text TEXT NOT NULL,
    claim_type TEXT CHECK (claim_type IN ('factual', 'normative', 'worldview')),

    -- For semantic search
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small

    -- Classification
    strength FLOAT CHECK (strength >= 0 AND strength <= 1),
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),

    -- Type-specific fields
    is_verifiable BOOLEAN,
    verification_status TEXT,
    fact_check_result JSONB,

    normative_type TEXT,
    implicit_values TEXT[],

    worldview_category TEXT,
    hidden_premises TEXT[],

    -- Cross-conversation relationships
    similar_claim_ids UUID[],  -- Claims with similar embeddings

    -- Metadata
    speaker_name TEXT,
    utterance_ids UUID[],
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX idx_claims_embedding ON claims
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Full-text search index
CREATE INDEX idx_claims_fulltext ON claims
USING gin(to_tsvector('english', claim_text));
```

#### 2. Claim Detection Service (Passive)

```python
# lct_python_backend/services/claim_detector.py

class ClaimDetector:
    """
    Passive claim extraction from conversations.
    Runs in background after conversation import.
    """

    async def analyze_conversation_passive(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Extract claims WITHOUT interrupting user.
        Store results for later search.
        """
        nodes = await self._get_nodes(conversation_id)

        all_claims = []
        for node in nodes:
            claims = await self._extract_claims(node)

            # Generate embeddings for semantic search
            for claim in claims:
                embedding = await self._get_embedding(claim["claim_text"])
                claim["embedding"] = embedding

                # Find similar claims across ALL conversations
                similar = await self._find_similar_claims(embedding)
                claim["similar_claim_ids"] = similar

            all_claims.extend(claims)
            await self._save_claims(claims)

        return {
            "conversation_id": conversation_id,
            "total_claims": len(all_claims),
            "by_type": self._aggregate_by_type(all_claims)
        }

    async def _find_similar_claims(
        self,
        embedding: List[float],
        threshold: float = 0.85
    ) -> List[str]:
        """
        Find semantically similar claims across ALL conversations.
        Uses vector similarity search.
        """
        query = """
        SELECT id, claim_text,
               1 - (embedding <=> $1::vector) as similarity
        FROM claims
        WHERE 1 - (embedding <=> $1::vector) > $2
        ORDER BY similarity DESC
        LIMIT 10
        """

        results = await self.db.execute(query, [embedding, threshold])
        return [row['id'] for row in results]
```

#### 3. Embedding Generation

```python
# lct_python_backend/services/embedding_service.py

import openai
from typing import List

class EmbeddingService:
    """Generate embeddings for semantic search."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",  # $0.02 / 1M tokens
            input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed for efficiency."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]
```

---

### Week 16: Argument Mapping & Is-Ought Detection

**Why This Matters**:
- Argument trees → Understand reasoning structure across conversations
- Is-ought conflations → Track philosophical consistency over time

#### 1. Argument Tree Extraction

```python
# lct_python_backend/services/argument_mapper.py

class ArgumentMapper:
    """
    Extract argument structures from conversations.
    Build premise → conclusion trees.
    """

    async def extract_argument_tree(
        self,
        conversation_id: str,
        node_id: str
    ) -> Dict[str, Any]:
        """
        Extract argument structure from node.

        Returns tree like:
        {
            "root_claim": "We should use approach X",
            "premises": [
                {
                    "claim": "Approach X is faster",
                    "evidence": ["Quote from speaker"],
                    "premises": [
                        {"claim": "Speed matters here", ...}
                    ]
                }
            ],
            "fallacies": ["circular_reasoning"],
            "is_valid": false
        }
        """
        # Get claims from node
        claims = await self._get_node_claims(node_id)

        # Use LLM to structure into tree
        tree = await self._build_tree_structure(claims)

        # Detect circular reasoning
        circular = self._detect_circular_dependencies(tree)

        # Check logical validity
        is_valid = self._check_validity(tree)

        return {
            "conversation_id": conversation_id,
            "node_id": node_id,
            "tree": tree,
            "circular_dependencies": circular,
            "is_valid": is_valid,
            "fallacies": self._detect_fallacies(tree)
        }
```

#### 2. Is-Ought Conflation Detector

```python
class IsOughtDetector:
    """
    Detect naturalistic fallacies (is → ought conflations).
    """

    async def detect_conflations(
        self,
        conversation_id: str
    ) -> List[Dict]:
        """
        Find instances where descriptive claims are used to justify normative claims.

        Example:
        - Descriptive: "Humans naturally seek wealth"
        - Normative: "Therefore capitalism is right"
        - Conflation: Jumping from is → ought
        """
        # Get all claims
        claims = await self._get_conversation_claims(conversation_id)

        factual = [c for c in claims if c.claim_type == 'factual']
        normative = [c for c in claims if c.claim_type == 'normative']

        conflations = []

        # Find temporal proximity (factual followed by normative)
        for i, fact in enumerate(factual):
            for norm in normative:
                if self._are_temporally_close(fact, norm):
                    # Use LLM to check if this is a conflation
                    is_conflation = await self._check_conflation(fact, norm)

                    if is_conflation["is_conflation"]:
                        conflations.append({
                            "descriptive_claim": fact.claim_text,
                            "normative_claim": norm.claim_text,
                            "explanation": is_conflation["explanation"],
                            "fallacy_type": is_conflation["fallacy_type"],
                            "confidence": is_conflation["confidence"]
                        })

        return conflations
```

---

## Phase 2: Cross-Conversation Infrastructure (Weeks 17-18)

### Goal
Enable search and connection across ALL conversations, not just one.

### Week 17: Semantic Search System

#### 1. Cross-Conversation Search API

```python
# lct_python_backend/services/cross_conversation_search.py

class CrossConversationSearch:
    """
    Search across entire conversation history.
    """

    async def semantic_search(
        self,
        query: str,
        search_type: str = "all",  # "claims", "nodes", "utterances"
        limit: int = 20
    ) -> List[Dict]:
        """
        Semantic search across all conversations.

        Args:
            query: Natural language query
            search_type: What to search (claims, nodes, full utterances)
            limit: Max results

        Returns:
            List of matches with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        if search_type == "claims":
            return await self._search_claims(query_embedding, limit)
        elif search_type == "nodes":
            return await self._search_nodes(query_embedding, limit)
        else:
            return await self._search_all(query_embedding, limit)

    async def _search_claims(
        self,
        embedding: List[float],
        limit: int
    ) -> List[Dict]:
        """Vector similarity search on claims."""
        query = """
        SELECT
            c.id,
            c.claim_text,
            c.claim_type,
            c.speaker_name,
            conv.title as conversation_title,
            conv.id as conversation_id,
            n.title as node_title,
            1 - (c.embedding <=> $1::vector) as similarity
        FROM claims c
        JOIN conversations conv ON c.conversation_id = conv.id
        JOIN nodes n ON c.node_id = n.id
        ORDER BY c.embedding <=> $1::vector
        LIMIT $2
        """

        results = await self.db.execute(query, [embedding, limit])
        return [dict(row) for row in results]

    async def keyword_search(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Full-text search for exact phrase matching.
        Complements semantic search.
        """
        query = """
        SELECT
            c.id,
            c.claim_text,
            conv.title as conversation_title,
            ts_rank(to_tsvector('english', c.claim_text),
                    plainto_tsquery('english', $1)) as rank
        FROM claims c
        JOIN conversations conv ON c.conversation_id = conv.id
        WHERE to_tsvector('english', c.claim_text) @@
              plainto_tsquery('english', $1)
        ORDER BY rank DESC
        LIMIT $2
        """

        results = await self.db.execute(query, [query, limit])
        return [dict(row) for row in results]

    async def faceted_search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 20
    ) -> List[Dict]:
        """
        Search with filters:
        - claim_type: factual/normative/worldview
        - speaker: specific person
        - date_range: time window
        - conversation_ids: specific conversations
        - implicit_values: normative claims with certain values
        """
        query_embedding = await self.embedding_service.embed_text(query)

        # Build dynamic query with filters
        conditions = ["1=1"]
        params = [query_embedding, limit]
        param_idx = 3

        if "claim_type" in filters:
            conditions.append(f"c.claim_type = ${param_idx}")
            params.append(filters["claim_type"])
            param_idx += 1

        if "speaker" in filters:
            conditions.append(f"c.speaker_name = ${param_idx}")
            params.append(filters["speaker"])
            param_idx += 1

        if "date_range" in filters:
            conditions.append(f"c.analyzed_at BETWEEN ${param_idx} AND ${param_idx + 1}")
            params.extend([filters["date_range"]["start"], filters["date_range"]["end"]])
            param_idx += 2

        if "implicit_values" in filters:
            conditions.append(f"c.implicit_values && ${param_idx}")
            params.append(filters["implicit_values"])
            param_idx += 1

        sql = f"""
        SELECT
            c.*,
            conv.title as conversation_title,
            1 - (c.embedding <=> $1::vector) as similarity
        FROM claims c
        JOIN conversations conv ON c.conversation_id = conv.id
        WHERE {' AND '.join(conditions)}
        ORDER BY c.embedding <=> $1::vector
        LIMIT $2
        """

        results = await self.db.execute(sql, params)
        return [dict(row) for row in results]
```

#### 2. API Endpoints

```python
# lct_python_backend/backend.py

@lct_app.get("/api/search/semantic")
async def semantic_search(
    query: str,
    search_type: str = "all",
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search across all conversations.

    Query examples:
    - "What have I said about AI alignment?"
    - "Find conversations about economic growth"
    - "Show me claims about fairness"
    """
    search_service = CrossConversationSearch(db)
    results = await search_service.semantic_search(query, search_type, limit)

    return {
        "query": query,
        "count": len(results),
        "results": results
    }


@lct_app.get("/api/search/faceted")
async def faceted_search(
    query: str,
    claim_type: Optional[str] = None,
    speaker: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    implicit_values: Optional[List[str]] = Query(None),
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Search with filters.

    Examples:
    - Find normative claims about "growth" with implicit value "efficiency"
    - Find factual claims by speaker "Alice" in last month
    """
    filters = {}
    if claim_type:
        filters["claim_type"] = claim_type
    if speaker:
        filters["speaker"] = speaker
    if date_start and date_end:
        filters["date_range"] = {"start": date_start, "end": date_end}
    if implicit_values:
        filters["implicit_values"] = implicit_values

    search_service = CrossConversationSearch(db)
    results = await search_service.faceted_search(query, filters, limit)

    return {
        "query": query,
        "filters": filters,
        "count": len(results),
        "results": results
    }


@lct_app.get("/api/conversations/{conversation_id}/related")
async def find_related_conversations(
    conversation_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Find conversations similar to this one.
    Uses claim embeddings to find semantic overlap.
    """
    # Get claims from this conversation
    claims = await get_conversation_claims(db, conversation_id)

    # Average embeddings
    avg_embedding = np.mean([c.embedding for c in claims], axis=0)

    # Find similar conversations
    query = """
    SELECT
        conv.id,
        conv.title,
        conv.created_at,
        AVG(1 - (c.embedding <=> $1::vector)) as avg_similarity,
        COUNT(c.id) as claim_count
    FROM conversations conv
    JOIN claims c ON c.conversation_id = conv.id
    WHERE conv.id != $2
    GROUP BY conv.id, conv.title, conv.created_at
    ORDER BY avg_similarity DESC
    LIMIT $3
    """

    results = await db.execute(query, [avg_embedding.tolist(), conversation_id, limit])

    return {
        "conversation_id": conversation_id,
        "related_conversations": [dict(row) for row in results]
    }
```

---

### Week 18: Knowledge Graph & Cross-References

**Goal**: Build explicit relationships between ideas across conversations.

#### 1. Cross-Conversation Knowledge Graph

```python
# lct_python_backend/services/knowledge_graph.py

class KnowledgeGraph:
    """
    Build graph of concepts across conversations.
    """

    async def build_concept_graph(self) -> Dict[str, Any]:
        """
        Extract concepts and relationships from ALL conversations.

        Returns graph like:
        {
            "nodes": [
                {"id": "ai_alignment", "type": "concept", "mentions": 45},
                {"id": "economic_growth", "type": "concept", "mentions": 23}
            ],
            "edges": [
                {"from": "ai_alignment", "to": "economic_growth",
                 "relationship": "related_to", "strength": 0.7}
            ]
        }
        """
        # Extract all claims
        all_claims = await self._get_all_claims()

        # Extract concepts from claims (using LLM)
        concepts = await self._extract_concepts(all_claims)

        # Find relationships between concepts
        edges = await self._find_concept_relationships(concepts)

        return {
            "nodes": concepts,
            "edges": edges,
            "metadata": {
                "total_conversations": await self._count_conversations(),
                "total_claims": len(all_claims),
                "total_concepts": len(concepts)
            }
        }

    async def trace_concept_evolution(
        self,
        concept: str
    ) -> List[Dict]:
        """
        Show how your thinking about a concept has evolved over time.

        Returns chronological list of claims about this concept.
        """
        # Find all claims mentioning concept
        query = """
        SELECT
            c.claim_text,
            c.claim_type,
            c.analyzed_at,
            conv.title as conversation_title,
            conv.created_at as conversation_date
        FROM claims c
        JOIN conversations conv ON c.conversation_id = conv.id
        WHERE to_tsvector('english', c.claim_text) @@
              plainto_tsquery('english', $1)
        ORDER BY c.analyzed_at ASC
        """

        results = await self.db.execute(query, [concept])
        return [dict(row) for row in results]
```

#### 2. Frontend: Global Search UI

```jsx
// lct_app/src/pages/GlobalSearch.jsx

import React, { useState } from 'react';
import { semanticSearch, facetedSearch } from '../services/searchApi';

export default function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [filters, setFilters] = useState({
    claimType: 'all',
    speaker: 'all',
  });

  const handleSearch = async () => {
    const searchResults = await semanticSearch(query, 'all', 20);
    setResults(searchResults);
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-4xl font-bold mb-6">Search All Conversations</h1>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="What have you discussed about AI alignment?"
            className="flex-1 px-4 py-3 border rounded-lg text-lg"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Search
          </button>
        </div>

        <div className="text-sm text-gray-600 mt-2">
          Try: "economic growth and fairness", "claims about AI safety", "normative statements by Alice"
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={filters.claimType}
          onChange={(e) => setFilters({...filters, claimType: e.target.value})}
          className="px-4 py-2 border rounded"
        >
          <option value="all">All Types</option>
          <option value="factual">Factual Claims</option>
          <option value="normative">Normative Claims</option>
          <option value="worldview">Worldview Claims</option>
        </select>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4">
          <div className="text-lg font-semibold">
            {results.count} results across {new Set(results.results.map(r => r.conversation_id)).size} conversations
          </div>

          {results.results.map(result => (
            <SearchResult key={result.id} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}

function SearchResult({ result }) {
  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50">
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm text-gray-500">
            {result.conversation_title}
          </span>
          <span className="mx-2 text-gray-300">→</span>
          <span className="text-sm text-gray-500">
            {result.node_title}
          </span>
        </div>
        <div className="text-sm text-gray-400">
          {(result.similarity * 100).toFixed(0)}% match
        </div>
      </div>

      <div className="text-lg mb-2">{result.claim_text}</div>

      <div className="flex gap-2">
        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
          {result.claim_type}
        </span>
        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm">
          {result.speaker_name}
        </span>
      </div>
    </div>
  );
}
```

---

## Phase 3: Entropy-Based Segmentation (Weeks 19-20)

### Goal
Find optimal conversation boundaries using information theory.

### Week 19: Entropy Measurement

**Concept**: Conversations have natural "joints" where topic/speaker/energy shifts. Measure information density to find these boundaries.

#### 1. Entropy Calculator

```python
# lct_python_backend/services/entropy_segmentation.py

import numpy as np
from typing import List, Tuple
from collections import Counter

class EntropySegmenter:
    """
    Find natural conversation boundaries using entropy.

    Measures:
    1. Topic entropy: How much does topic shift?
    2. Speaker entropy: How much does speaker distribution change?
    3. Semantic entropy: How much does meaning shift?
    """

    def calculate_segmentation_quality(
        self,
        utterances: List[Utterance],
        segments: List[Tuple[int, int]]  # (start_idx, end_idx) pairs
    ) -> Dict[str, float]:
        """
        Score quality of segmentation.

        Good segmentation = high entropy BETWEEN segments, low entropy WITHIN segments
        """
        inter_segment_entropy = self._calculate_inter_segment_entropy(utterances, segments)
        intra_segment_entropy = self._calculate_intra_segment_entropy(utterances, segments)

        # Quality score: maximize between-segment entropy, minimize within-segment
        quality = inter_segment_entropy / (intra_segment_entropy + 1e-6)

        return {
            "quality_score": quality,
            "inter_segment_entropy": inter_segment_entropy,
            "intra_segment_entropy": intra_segment_entropy
        }

    def find_optimal_boundaries(
        self,
        utterances: List[Utterance],
        min_segment_length: int = 3,
        max_segment_length: int = 20
    ) -> List[int]:
        """
        Find optimal segmentation boundaries using dynamic programming.

        Returns list of boundary indices.
        """
        n = len(utterances)

        # Calculate entropy at each possible boundary
        boundary_scores = []
        for i in range(min_segment_length, n - min_segment_length):
            entropy_drop = self._calculate_entropy_drop(utterances, i)
            boundary_scores.append((i, entropy_drop))

        # Sort by entropy drop (higher = better boundary)
        boundary_scores.sort(key=lambda x: x[1], reverse=True)

        # Greedily select boundaries
        boundaries = []
        for idx, score in boundary_scores:
            # Check if this boundary conflicts with existing ones
            if not self._conflicts_with_existing(idx, boundaries, min_segment_length):
                boundaries.append(idx)

        return sorted(boundaries)

    def _calculate_entropy_drop(
        self,
        utterances: List[Utterance],
        boundary_idx: int
    ) -> float:
        """
        Calculate entropy drop at this boundary.

        Combines:
        - Topic shift (semantic similarity drop)
        - Speaker shift
        - Pause duration
        """
        # Get embeddings
        before_embedding = self._get_segment_embedding(utterances[:boundary_idx])
        after_embedding = self._get_segment_embedding(utterances[boundary_idx:])

        # Semantic discontinuity
        semantic_drop = 1 - self._cosine_similarity(before_embedding, after_embedding)

        # Speaker change
        speaker_before = utterances[boundary_idx - 1].speaker_name
        speaker_after = utterances[boundary_idx].speaker_name
        speaker_change = 1.0 if speaker_before != speaker_after else 0.0

        # Time gap
        time_gap = utterances[boundary_idx].start_time - utterances[boundary_idx - 1].end_time
        time_score = min(time_gap / 10.0, 1.0)  # Normalize to [0, 1]

        # Combine scores
        return (0.6 * semantic_drop + 0.2 * speaker_change + 0.2 * time_score)

    def _calculate_inter_segment_entropy(
        self,
        utterances: List[Utterance],
        segments: List[Tuple[int, int]]
    ) -> float:
        """
        Measure diversity BETWEEN segments.
        High value = segments are different from each other.
        """
        segment_embeddings = []
        for start, end in segments:
            embedding = self._get_segment_embedding(utterances[start:end+1])
            segment_embeddings.append(embedding)

        # Calculate pairwise distances
        distances = []
        for i in range(len(segment_embeddings)):
            for j in range(i + 1, len(segment_embeddings)):
                dist = 1 - self._cosine_similarity(
                    segment_embeddings[i],
                    segment_embeddings[j]
                )
                distances.append(dist)

        return np.mean(distances) if distances else 0.0

    def _calculate_intra_segment_entropy(
        self,
        utterances: List[Utterance],
        segments: List[Tuple[int, int]]
    ) -> float:
        """
        Measure diversity WITHIN segments.
        Low value = segments are internally coherent.
        """
        within_variances = []
        for start, end in segments:
            segment_utts = utterances[start:end+1]

            if len(segment_utts) < 2:
                continue

            # Get embeddings for utterances in segment
            embeddings = [self._get_utterance_embedding(u) for u in segment_utts]

            # Calculate variance within segment
            variance = np.var(embeddings, axis=0).mean()
            within_variances.append(variance)

        return np.mean(within_variances) if within_variances else 0.0
```

#### 2. Segmentation Comparison UI

```jsx
// lct_app/src/pages/SegmentationQuality.jsx

export default function SegmentationQuality({ conversationId }) {
  const [currentSegmentation, setCurrentSegmentation] = useState(null);
  const [proposedSegmentation, setProposedSegmentation] = useState(null);
  const [quality, setQuality] = useState(null);

  const analyzeSegmentation = async () => {
    // Get current segmentation (from LLM)
    const current = await getCurrentSegmentation(conversationId);

    // Get entropy-optimal segmentation
    const proposed = await getEntropyOptimalSegmentation(conversationId);

    // Compare quality
    const comparison = await compareSegmentations(
      conversationId,
      current,
      proposed
    );

    setCurrentSegmentation(current);
    setProposedSegmentation(proposed);
    setQuality(comparison);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Segmentation Quality Analysis</h2>

      {quality && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="border rounded-lg p-4">
            <h3 className="font-semibold mb-2">Current (LLM)</h3>
            <div className="text-3xl font-bold text-blue-600">
              {quality.current.quality_score.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">
              {current Segmentation.segments.length} segments
            </div>
          </div>

          <div className="border rounded-lg p-4">
            <h3 className="font-semibold mb-2">Entropy-Optimal</h3>
            <div className="text-3xl font-bold text-green-600">
              {quality.proposed.quality_score.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">
              {proposedSegmentation.segments.length} segments
            </div>
          </div>
        </div>
      )}

      <button
        onClick={analyzeSegmentation}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Analyze Segmentation Quality
      </button>
    </div>
  );
}
```

---

### Week 20: Adaptive Segmentation

**Goal**: Use entropy measurements to improve LLM segmentation prompts.

#### 1. Feedback Loop

```python
class AdaptiveSegmenter:
    """
    Learn optimal segmentation from entropy analysis.
    """

    async def improve_segmentation(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Re-segment conversation using entropy-informed prompts.
        """
        # Get current segmentation
        current_nodes = await self._get_nodes(conversation_id)

        # Calculate entropy quality
        entropy_segmenter = EntropySegmenter()
        boundaries = entropy_segmenter.find_optimal_boundaries(utterances)

        # If entropy suggests different boundaries, re-prompt LLM
        if self._should_resegment(current_nodes, boundaries):
            # Regenerate with hints about entropy boundaries
            new_nodes = await self._resegment_with_hints(
                conversation_id,
                boundaries
            )

            return {
                "resegmented": True,
                "old_node_count": len(current_nodes),
                "new_node_count": len(new_nodes),
                "quality_improvement": "..."
            }

        return {"resegmented": False}
```

---

## Cost Estimation

### Per-Conversation Analysis Costs

**Week 15-16 (Claims & Arguments)**:
- Claim detection: 50 nodes × $0.015 = **$0.75**
- Argument mapping: 10 trees × $0.02 = **$0.20**
- **Total: ~$1.00 per conversation**

**Week 17-18 (Embeddings & Search)**:
- Initial embedding generation: 100 claims × ($0.02 / 1000) = **$0.002**
- Ongoing: Negligible (cached)
- **Total: ~$0.01 per conversation**

**Week 19-20 (Entropy)**:
- Entropy calculation: Pure math, no API calls = **$0.00**
- Optional re-segmentation: $0.75 if triggered
- **Total: ~$0.00 - $0.75 per conversation**

### For 1000 Conversations

- Initial analysis: **$1,000**
- Ongoing search: Minimal (vector DB lookups)
- Storage: ~5GB (embeddings + claims)

---

## Success Metrics

1. **Search Relevance**
   - Top-5 accuracy: >80% for semantic search
   - User feedback: "Was this helpful?" >70% yes

2. **Segmentation Quality**
   - Entropy-based quality score: >0.7
   - User edit rate: <15% of segments manually adjusted

3. **Cross-Conversation Insights**
   - % of searches that span multiple conversations: >60%
   - User engagement with "Related Conversations": >40% click-through

4. **Performance**
   - Search latency: <500ms for semantic search
   - Embedding generation: <2s per conversation
   - Entropy calculation: <5s per conversation

---

## Integration Summary

### How This Fits Together

```
Week 15-16: Extract structured knowledge (claims, arguments)
    ↓
Week 17: Make it searchable (embeddings, vector DB)
    ↓
Week 18: Connect across conversations (knowledge graph)
    ↓
Week 19-20: Optimize boundaries (entropy-based segmentation)
```

### User Journey

1. **Import conversations** → Passive analysis begins
2. **Search**: "What have I said about AI safety?"
3. **Discover**: Find 20 claims across 5 conversations
4. **Explore**: Click to see argument trees
5. **Connect**: View related conversations
6. **Refine**: Adjust segmentation based on entropy

---

## Next Steps

After these 6 weeks:
- **Perplexity Integration** (Week 21): Real-time fact-checking for factual claims
- **Double Crux** (Week 22): Find underlying disagreements
- **Temporal Analysis** (Week 23): Track concept evolution over time
- **Export/Integration** (Week 24): Obsidian deep integration

Ready to proceed with implementation?
