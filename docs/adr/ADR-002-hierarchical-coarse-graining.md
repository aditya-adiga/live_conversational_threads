# ADR-002: Hierarchical Coarse-Graining for Multi-Scale Graph Visualization

**Status**: Proposed
**Date**: 2025-11-10
**Deciders**: Development Team
**Related**: ADR-001 (Google Meet Transcripts)

## Context and Problem Statement

The current conversation graph becomes visually overwhelming for long conversations. All nodes are displayed at the same granularity level, making it impossible to:

1. **See the big picture**: Zoom out to view major themes without visual clutter
2. **Navigate efficiently**: Jump between high-level topics and detailed nodes
3. **Understand hierarchy**: No way to show that some nodes are sub-topics of others
4. **Scale gracefully**: Graph complexity grows linearly with conversation length

**User Need**: "If I zoom out, I want to see just the main three threads. If I zoom in, that node should break up into sub-nodes."

## Current Data Model Limitations

**Existing Structure:**
```python
{
  "node_name": "API Design Discussion",
  "predecessor": "Sprint Planning",
  "successor": "Database Schema",
  "contextual_relation": {
    "Security Concerns": "Both discuss authentication"
  },
  "linked_nodes": ["Security Concerns"]
}
```

**Problems:**
- ❌ No parent/child relationships
- ❌ No hierarchy levels
- ❌ No clustering metadata
- ❌ All nodes at same granularity
- ❌ No way to aggregate related nodes

## Decision Drivers

1. **Visual Scalability**: Must handle 100+ node conversations
2. **User Control**: Users should control zoom level and clustering
3. **Semantic Coherence**: Clusters must be topically meaningful
4. **Performance**: Rendering must be fast at all zoom levels
5. **Backward Compatibility**: Existing conversations should still work
6. **Edit-Friendly**: Users must be able to manually adjust clusters

## Proposed Solution: Multi-Level Hierarchical Graph

### Conceptual Model

```
Level 3 (Themes):     [Product Strategy]
                              |
Level 2 (Topics):     [Feature Planning] --- [Technical Decisions]
                           /    |    \           /         \
Level 1 (Nodes):   [UI/UX] [API] [DB]    [Security]   [Performance]
                      |      |     |          |             |
Level 0 (Utterances): Individual speaker turns (not shown in graph)
```

### Data Model Changes

**Enhanced Node Structure:**
```python
{
  "node_name": "API Design Discussion",
  "node_id": "uuid-1234",  # NEW: Unique identifier
  "level": 1,  # NEW: Hierarchy level (0=utterance, 1=node, 2=topic, 3=theme)
  "parent_id": "uuid-parent",  # NEW: Parent cluster ID
  "children_ids": ["uuid-child1", "uuid-child2"],  # NEW: Child nodes

  # Existing fields
  "predecessor": "uuid-predecessor",
  "successor": "uuid-successor",
  "contextual_relation": {...},
  "linked_nodes": [...],

  # NEW: Aggregation metadata
  "cluster_info": {
    "auto_clustered": true,  # Was this auto-generated or user-created?
    "cluster_algorithm": "semantic_similarity",  # How was it created?
    "cluster_confidence": 0.85,  # Confidence score
    "sub_node_count": 5,  # How many nodes does this aggregate?
    "summary": "High-level summary of all child nodes",
    "key_claims": ["claim1", "claim2"],  # Most important claims from children
    "dominant_speakers": ["Speaker 1", "Speaker 2"]  # If using speaker info
  },

  # NEW: Visual metadata
  "display_preferences": {
    "collapse_threshold": 2,  # At what zoom level to collapse this node?
    "color": "auto",  # Can be overridden by user
    "icon": "topic",  # Visual indicator of node type
    "pinned": false  # User wants this always visible
  }
}
```

### Hierarchy Levels

| Level | Name | Description | Example | Typical Count |
|-------|------|-------------|---------|---------------|
| 0 | Utterance | Individual speaker turns | "I think we should use GraphQL" | 1000+ |
| 1 | Node | Current conversation nodes | "API Design Discussion" | 50-100 |
| 2 | Topic | Clustered related nodes | "Technical Architecture" | 5-15 |
| 3 | Theme | Major conversation themes | "Product Strategy" | 2-5 |

## Implementation Strategy

### Phase 1: Data Model & Auto-Clustering

**1.1 Add Hierarchy Fields**
```python
class ConversationNode:
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: int = 1  # Default to current level
    parent_id: Optional[str] = None
    children_ids: List[str] = []
    cluster_info: Optional[ClusterInfo] = None
    display_preferences: DisplayPreferences = DisplayPreferences()
```

**1.2 Automatic Clustering Algorithm**
```python
def auto_cluster_nodes(nodes: List[Node], target_level: int = 2) -> List[Node]:
    """
    Cluster nodes into higher-level aggregates using semantic similarity.

    Algorithm:
    1. Embed all node summaries using sentence-transformers
    2. Apply hierarchical clustering (ward linkage)
    3. Cut dendrogram at appropriate height for target cluster count
    4. Generate cluster summaries using LLM
    5. Preserve temporal and contextual relationships
    """
    # Embed summaries
    embeddings = embed_summaries([n.summary for n in nodes])

    # Hierarchical clustering
    linkage_matrix = hierarchy.linkage(embeddings, method='ward')
    cluster_labels = hierarchy.fcluster(linkage_matrix,
                                        t=target_cluster_count,
                                        criterion='maxclust')

    # Create parent nodes
    clusters = defaultdict(list)
    for node, label in zip(nodes, cluster_labels):
        clusters[label].append(node)

    parent_nodes = []
    for cluster_id, child_nodes in clusters.items():
        parent = create_cluster_node(child_nodes, level=2)
        parent_nodes.append(parent)

    return parent_nodes
```

**1.3 LLM-Based Cluster Summarization**
```python
def create_cluster_node(children: List[Node], level: int) -> Node:
    """
    Use LLM to create a meaningful summary node for a cluster.
    """
    prompt = f"""
    You are aggregating {len(children)} conversation nodes into a single
    higher-level summary node.

    Child nodes:
    {format_nodes(children)}

    Create a cluster summary with:
    1. Concise name (3-5 words) capturing the common theme
    2. Summary (2-3 sentences) covering main points
    3. Key claims (top 3 most important from all children)
    4. Temporal flow (preserve predecessor/successor at this level)

    Output JSON format: {{name, summary, key_claims, ...}}
    """

    response = llm_call(prompt)
    return Node(**response, level=level, children_ids=[c.node_id for c in children])
```

### Phase 2: Frontend Zoom Controls

**2.1 Zoom Level State Management**
```javascript
const [zoomLevel, setZoomLevel] = useState(1); // 0=utterances, 1=nodes, 2=topics, 3=themes

// Filter nodes based on zoom level
const visibleNodes = useMemo(() => {
  return graphData.filter(node =>
    node.level === zoomLevel || node.display_preferences.pinned
  );
}, [graphData, zoomLevel]);
```

**2.2 Zoom UI Component**
```jsx
<ZoomControl>
  <button onClick={() => setZoomLevel(3)}>Themes Only</button>
  <Slider
    min={0}
    max={3}
    value={zoomLevel}
    onChange={setZoomLevel}
    labels={["Utterances", "Nodes", "Topics", "Themes"]}
  />
  <button onClick={() => setZoomLevel(0)}>All Details</button>
</ZoomControl>
```

**2.3 Interactive Expand/Collapse**
```jsx
const ExpandableNode = ({ node }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    if (node.children_ids.length > 0) {
      setIsExpanded(!isExpanded);
      // Fetch and display child nodes
      loadChildNodes(node.children_ids);
    }
  };

  return (
    <Node onClick={handleClick}>
      <NodeTitle>{node.node_name}</NodeTitle>
      {node.children_ids.length > 0 && (
        <ExpandIcon>{isExpanded ? "−" : "+"} ({node.cluster_info.sub_node_count})</ExpandIcon>
      )}
    </Node>
  );
};
```

**2.4 Smooth Transitions**
```css
/* Animate node expansion/collapse */
.node {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.node.expanding {
  transform: scale(1.05);
  opacity: 0;
}

.child-nodes {
  animation: fadeIn 0.4s ease-in;
}
```

### Phase 3: Manual Clustering Controls

**3.1 Drag-to-Cluster**
```jsx
const handleDragEnd = (event) => {
  const { active, over } = event;

  if (over && over.id === 'cluster-zone') {
    // User dragged a node to the cluster area
    const selectedNodes = getSelectedNodes();
    createManualCluster(selectedNodes);
  }
};

function createManualCluster(nodes) {
  const clusterName = prompt("Name this cluster:");

  fetch('/api/create-cluster/', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      node_ids: nodes.map(n => n.node_id),
      cluster_name: clusterName,
      level: 2
    })
  });
}
```

**3.2 Context Menu Actions**
```jsx
<ContextMenu>
  <MenuItem onClick={() => clusterSelected()}>
    🔗 Cluster Selected Nodes
  </MenuItem>
  <MenuItem onClick={() => unclusterNode(node)}>
    🔓 Uncluster / Show Children
  </MenuItem>
  <MenuItem onClick={() => moveToCluster(node, targetCluster)}>
    📦 Move to Different Cluster
  </MenuItem>
  <MenuItem onClick={() => promoteNode(node)}>
    ⬆️ Promote to Higher Level
  </MenuItem>
  <MenuItem onClick={() => pinNode(node)}>
    📌 Pin (Always Visible)
  </MenuItem>
</ContextMenu>
```

### Phase 4: API Endpoints

**Create Cluster:**
```
POST /api/conversations/{id}/create-cluster/

Request:
{
  "node_ids": ["uuid1", "uuid2", "uuid3"],
  "cluster_name": "Feature Planning",
  "level": 2,
  "auto_summarize": true
}

Response:
{
  "cluster_node": { ... },
  "updated_children": [ ... ]
}
```

**Auto-Cluster Conversation:**
```
POST /api/conversations/{id}/auto-cluster/

Request:
{
  "target_level": 2,
  "method": "semantic_similarity" | "temporal_proximity" | "speaker_based",
  "cluster_count": 5,  // Approximate desired number of clusters
  "preserve_bookmarks": true  // Keep bookmarked nodes at original level
}

Response:
{
  "cluster_nodes": [ ... ],
  "clustering_confidence": 0.82,
  "suggestions": [
    {
      "node_ids": ["uuid1", "uuid2"],
      "reason": "Both discuss authentication",
      "confidence": 0.9
    }
  ]
}
```

**Update Cluster:**
```
PATCH /api/conversations/{id}/clusters/{cluster_id}/

Request:
{
  "add_children": ["uuid-new"],
  "remove_children": ["uuid-old"],
  "update_summary": "New summary text"
}
```

## Layout Algorithm for Multi-Level Graphs

### Hierarchical Layout Strategy

```python
def calculate_hierarchical_layout(nodes: List[Node], zoom_level: int):
    """
    Layout nodes based on current zoom level.

    Principles:
    1. Higher-level nodes are larger and more spaced
    2. Temporal flow still left-to-right within each level
    3. Parent nodes positioned as centroid of children
    4. Smooth transitions when expanding/collapsing
    """

    # Filter visible nodes by zoom level
    visible_nodes = [n for n in nodes if n.level == zoom_level or n.pinned]

    if zoom_level >= 2:
        # Topics/Themes: Grid layout with large spacing
        return grid_layout(visible_nodes, spacing=600, node_size=400)
    else:
        # Nodes: Flow layout (current behavior)
        return hierarchical_flow_layout(visible_nodes, spacing=400, node_size=350)
```

### Visual Encoding

| Zoom Level | Node Size | Spacing | Edge Thickness | Label Size |
|------------|-----------|---------|----------------|------------|
| 3 (Themes) | 500px | 800px | 4px | 24pt |
| 2 (Topics) | 400px | 600px | 3px | 18pt |
| 1 (Nodes) | 350px | 400px | 2px | 14pt |
| 0 (Utterances) | 200px | 250px | 1px | 10pt |

## Edge Handling Across Levels

**Problem**: When nodes are clustered, what happens to edges?

**Solution**: Edge Aggregation Rules

```python
def aggregate_edges(parent_node: Node):
    """
    When clustering nodes, aggregate their edges.

    Rules:
    1. Temporal edges: Parent's predecessor/successor = first/last child's
    2. Contextual edges: Aggregate all unique contextual relations
    3. Edge strength: Proportional to number of child edges
    """
    children = get_children(parent_node)

    # Temporal
    parent_node.predecessor = children[0].predecessor
    parent_node.successor = children[-1].successor

    # Contextual
    all_relations = {}
    for child in children:
        for target, explanation in child.contextual_relation.items():
            # If target is also a child of this cluster, skip (internal edge)
            if target not in [c.node_name for c in children]:
                all_relations[target] = explanation

    parent_node.contextual_relation = all_relations

    # Edge weights (for visualization)
    edge_weights = count_edge_frequency(children)
    parent_node.edge_metadata = {"weights": edge_weights}
```

**Visual Representation**:
- **Thick edges**: Many child edges between clusters
- **Thin edges**: Few connections
- **Dashed edges**: Mixed relationship types

## Clustering Methods

### 1. Semantic Similarity (Default)
- Embed node summaries using sentence-transformers
- Use cosine similarity + hierarchical clustering
- Best for: Thematic grouping

### 2. Temporal Proximity
- Cluster consecutive nodes in time
- Use sliding window approach
- Best for: Chronological narrative

### 3. Speaker-Based
- Cluster by dominant speaker
- Best for: Multi-party conversations, tracking individual contributions

### 4. Claim-Based
- Cluster nodes with similar claim types
- Best for: Argument analysis, debate structure

### 5. User-Defined
- Manual clustering via drag-and-drop
- Best for: Domain-specific organization

## Backward Compatibility

**Handling Existing Conversations:**

```python
def migrate_to_hierarchical(conversation):
    """
    Convert flat graph to hierarchical structure.

    Strategy:
    1. All existing nodes become level=1 (nodes)
    2. Auto-cluster to generate level=2 (topics)
    3. Generate level=3 (themes) if >10 topics
    4. Preserve all existing relationships
    """
    for node in conversation.graph_data[0]:
        node['node_id'] = str(uuid.uuid4())  # Add IDs if missing
        node['level'] = 1
        node['parent_id'] = None
        node['children_ids'] = []

    # Auto-cluster if >20 nodes
    if len(conversation.graph_data[0]) > 20:
        auto_cluster_nodes(conversation, target_level=2)
```

**UI Fallback:**
- Conversations without hierarchy display at zoom_level=1 (current behavior)
- "Auto-Cluster" button available for old conversations
- One-click migration with preview

## Performance Considerations

**Rendering Optimization:**
```javascript
// Only render visible nodes + immediate neighbors
const getRenderSet = (visibleNodes, zoom_level) => {
  const renderSet = new Set(visibleNodes);

  // Add parent if showing children
  if (zoom_level < 2) {
    visibleNodes.forEach(node => {
      if (node.parent_id) renderSet.add(node.parent_id);
    });
  }

  // Add children if parent is expanded
  visibleNodes.forEach(node => {
    if (node.isExpanded) {
      node.children_ids.forEach(childId => renderSet.add(childId));
    }
  });

  return Array.from(renderSet);
};
```

**Lazy Loading:**
- Load level 2+ nodes on initial page load
- Load level 1 nodes only when parent is expanded
- Load level 0 (utterances) only when specifically requested

## Success Metrics

1. **Visual Clarity**: Users can understand 100+ node conversations at a glance
2. **Navigation Speed**: <2 clicks to reach any node from theme view
3. **Clustering Quality**: >80% user acceptance of auto-clustering
4. **Performance**: <200ms to expand/collapse at any zoom level
5. **User Adoption**: 60%+ of users with >20 nodes use clustering

## Open Questions

1. **Default zoom level**: Start at themes or nodes?
2. **Animation speed**: How long for expand/collapse transitions?
3. **Cluster count**: What's the ideal number of topics for readability?
4. **Mobile experience**: How to handle zoom on small screens?
5. **Collaboration**: How do multiple users coordinate clustering?
6. **Version control**: Track history of clustering changes?

## Future Enhancements

1. **ML-Powered Suggestions**: "These 3 nodes should probably be clustered"
2. **Saved Views**: Users can save and share different clustering schemes
3. **Cluster Templates**: Pre-defined patterns for common conversation types
4. **Animated Narrative Mode**: Auto-play through clusters with zoom animations
5. **Cluster Diff**: Compare clustering across conversation versions

## References

- [Hierarchical Graph Visualization](https://ieeexplore.ieee.org/document/7194834)
- [Hierarchical Clustering Algorithms](https://scikit-learn.org/stable/modules/clustering.html#hierarchical-clustering)
- [Sentence-BERT for Semantic Similarity](https://arxiv.org/abs/1908.10084)
- [Zoom-Dependent Graph Rendering](https://observablehq.com/@d3/zoom-to-bounding-box)
