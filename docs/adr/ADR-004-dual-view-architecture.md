# ADR-004: Dual-View Architecture for Conversation Visualization

**Status**: Approved
**Date**: 2025-11-11
**Deciders**: Product Team, UX Design
**Related**: ADR-002 (Hierarchical Coarse-Graining)

## Context and Problem Statement

The current conversation graph visualization presents nodes in a single view, making it difficult for users to simultaneously understand:

1. **Temporal flow**: When things were said, in chronological order
2. **Contextual relationships**: How ideas relate thematically, regardless of time
3. **Navigation context**: Where you are in the conversation timeline vs. the idea space

**User Need**: "I want to see the timeline of who said what when, AND the thematic clustering of related ideas, at the same time. I shouldn't have to toggle between views."

**Key Insight from User Research**:
- Users naturally think about conversations in two dimensions:
  - **Linear/temporal**: "What happened first, then next, then after that?"
  - **Networked/contextual**: "What ideas are related? What topics branch off from this?"
- Forcing users to choose one view at a time breaks their mental model

## Current Limitations

**Single-View Approach:**
```
Current UI:
┌─────────────────────────────┐
│  [Toggle: Temporal | Graph] │ ← User must choose
│                             │
│    All nodes in one view    │
│                             │
│                             │
└─────────────────────────────┘
```

**Problems:**
- ❌ Cannot see temporal order while exploring contextual relationships
- ❌ No visual anchor showing "where am I in time?"
- ❌ Difficult to understand narrative flow vs. idea clustering
- ❌ Context switching overhead (mental effort to remember what was in other view)

## Decision Drivers

1. **Cognitive Load Reduction**: Minimize view switching and mental context retention
2. **Spatial Consistency**: Temporal position should always be visible as reference
3. **Screen Real Estate**: Maximize space for the more complex contextual view
4. **Interaction Design**: Allow independent interaction with each view while maintaining synchronization
5. **Scalability**: Must work for conversations with 100+ nodes
6. **Accessibility**: Clear visual separation, keyboard navigation support

## Proposed Solution: Dual-View Split Canvas

### Visual Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│         CONTEXTUAL NETWORK VIEW             │
│                                             │
│     [Thematic clustering, idea graph]       │
│                                             │  85% of vertical space
│  ┌───┐     ┌───┐                           │
│  │   │────→│   │                           │
│  └───┘     └───┘                           │
│      ↘     ↗                               │
│       ┌───┐                                │
│       │   │                                │
│       └───┘                                │
│                                             │
├─────────────────────────────────────────────┤ ← Resizable divider
│  TIMELINE VIEW                              │
│  [Temporal sequence, speaker order]         │  15% of vertical space
│  ●───●───●───●───●───●───●───●───●──→      │
│  └┬┘ └┬┘ └┬┘ └┬┘ └┬┘ └┬┘ └┬┘ └┬┘ └┬┘      │
│   A   B   A   C   B   A   C   B   A        │
└─────────────────────────────────────────────┘
```

### Spatial Allocation

| View                     | Default Height | Min Height | Max Height | Purpose                                    |
|--------------------------|----------------|------------|------------|--------------------------------------------|
| Contextual Network View  | 85%            | 60%        | 90%        | Primary workspace for exploring ideas      |
| Timeline View            | 15%            | 10%        | 40%        | Temporal context and navigation            |

**Rationale for 85/15 Split:**
- Contextual view is more complex, needs space for graph layout
- Timeline is inherently linear, efficient use of horizontal space
- Most user time spent exploring contextual relationships
- Timeline serves as reference/anchor, not primary focus

**User-Adjustable:**
- Divider can be dragged to resize (10-40% for timeline)
- Preference saved per user
- Both views collapse gracefully on small screens

## Detailed Design

### Timeline View (Bottom 15%)

**Visual Design:**
```
Timeline Layout:
┌────────────────────────────────────────────────────────────┐
│  [Zoom: ━━━●━━━]  [Speed: 1x ▼]  [▶ Play] [⏸ Pause]       │
│                                                            │
│  00:00                                               45:30 │
│  ●─────●────●──────●───────●─────●──────●─────●────────●  │
│  │     │    │      │       │     │      │     │        │  │
│  A     B    A      C       B     A      C     B        A  │
│                                                ▲           │
│                                                │           │
│                                        Current position    │
└────────────────────────────────────────────────────────────┘
```

**Components:**
1. **Horizontal Timeline**: Linear progression, left-to-right
2. **Node Markers**: Dots representing each utterance or node
3. **Speaker Labels**: Below markers (color-coded)
4. **Current Position Indicator**: Highlighted marker showing focus
5. **Playback Controls**: Auto-advance through conversation
6. **Zoom Control**: Compress/expand time scale

**Interaction Behaviors:**
- **Click marker**: Jump to that node in contextual view
- **Drag timeline**: Scrub through conversation
- **Hover marker**: Show tooltip with summary
- **Select range**: Highlight multiple nodes for analysis

**Information Density:**
- At sentence level (zoom 1): Every utterance visible
- At turn level (zoom 2): Aggregate by speaker turn
- At topic level (zoom 3): Only show topic boundaries
- At theme level (zoom 4+): Major conversation milestones

### Contextual Network View (Top 85%)

**Visual Design:**
```
Network Layout:
┌────────────────────────────────────────────────────────────┐
│  [Edit Mode: OFF ▼] [Layout: Force ▼] [Zoom: ━━●━━] [⚙]   │
│                                                            │
│         ┌────────────────┐                                │
│         │ Product Vision │ ← Theme node (zoom 5)          │
│         └────────┬───────┘                                │
│                  │                                        │
│          ┌───────┴──────┐                                │
│   ┌──────▼─────┐  ┌─────▼──────┐                        │
│   │  Features  │  │ Architecture│ ← Topic nodes (zoom 3)  │
│   └──────┬─────┘  └─────┬──────┘                        │
│          │              │                                │
│     ┌────┼────┐    ┌────┼────┐                          │
│  ┌──▼─┐ ┌▼──┐│ ┌──▼─┐ ┌▼──┐                            │
│  │UI  │ │API││ │DB  │ │Auth│ ← Regular nodes (zoom 1)    │
│  └────┘ └───┘│ └────┘ └───┘                            │
│              │                                           │
│         ┌────▼────┐                                      │
│         │Security │ ← Cross-cutting concern              │
│         └─────────┘                                      │
│    (dashed edges = contextual relationships)             │
└────────────────────────────────────────────────────────────┘
```

**Components:**
1. **Node Graph**: Hierarchical, force-directed layout
2. **Temporal Edges**: Solid arrows showing predecessor/successor
3. **Contextual Edges**: Dashed lines showing thematic relationships
4. **Clusters**: Visual grouping at higher zoom levels
5. **Node Detail Panel**: Slide-in panel on the right (optional)

**Layout Algorithms:**
- **Force-directed**: Default, natural clustering
- **Hierarchical**: Top-down tree layout
- **Radial**: Circular layout centered on selected node
- **Timeline-aligned**: Nodes positioned by temporal order (hybrid)

**Zoom Synchronization:**
- Timeline zoom level determines which nodes visible in network view
- Zooming in timeline automatically expands corresponding clusters in network
- Inverse: Expanding cluster in network highlights timespan in timeline

### Synchronization Behaviors

**Bidirectional Linking:**

| Action in Timeline View          | Effect in Contextual View              |
|----------------------------------|----------------------------------------|
| Click node marker                | Center and highlight that node         |
| Drag timeline position           | Update "current position" highlight    |
| Select time range                | Highlight all nodes in that range      |
| Play animation                   | Auto-highlight nodes sequentially      |

| Action in Contextual View        | Effect in Timeline View                |
|----------------------------------|----------------------------------------|
| Select node                      | Highlight position in timeline         |
| Expand cluster                   | Show child node markers in timeline    |
| Filter by speaker                | Dim other speaker markers in timeline  |
| Hover edge                       | Highlight source/target times          |

**Visual Synchronization Cues:**
```typescript
// Synchronized highlighting example
const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

// Timeline view
<TimelineMarker
  nodeId={node.id}
  isSelected={selectedNodeId === node.id}
  onClick={() => setSelectedNodeId(node.id)}
  className={selectedNodeId === node.id ? "ring-blue-500" : ""}
/>

// Contextual view
<NetworkNode
  nodeId={node.id}
  isSelected={selectedNodeId === node.id}
  className={selectedNodeId === node.id ? "shadow-lg scale-110" : ""}
/>
```

## Implementation Strategy

### Phase 1: Split Canvas Layout (Week 5, Days 1-3)

**React Component Structure:**
```typescript
// src/components/DualView/DualViewCanvas.tsx

export const DualViewCanvas: React.FC = () => {
  const [dividerPosition, setDividerPosition] = useState(0.85); // 85% top, 15% bottom
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>(3); // Topic level

  return (
    <div className="dual-view-container">
      <ContextualNetworkView
        height={`${dividerPosition * 100}%`}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
        zoomLevel={zoomLevel}
      />

      <ResizableDivider
        position={dividerPosition}
        onResize={setDividerPosition}
      />

      <TimelineView
        height={`${(1 - dividerPosition) * 100}%`}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
        zoomLevel={zoomLevel}
        onZoomChange={setZoomLevel}
      />
    </div>
  );
};
```

**CSS Layout:**
```css
.dual-view-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.contextual-network-view {
  flex: 1;
  min-height: 60%;
  background: var(--bg-graph);
  border-bottom: 2px solid var(--border-divider);
}

.timeline-view {
  flex: 0 0 auto;
  min-height: 10%;
  max-height: 40%;
  background: var(--bg-timeline);
  overflow-x: auto;
  overflow-y: hidden;
}

.resizable-divider {
  height: 4px;
  background: var(--border-divider);
  cursor: ns-resize;
  user-select: none;
  transition: background 0.2s;
}

.resizable-divider:hover {
  background: var(--accent-primary);
}
```

### Phase 2: Timeline View Implementation (Week 5, Days 4-5)

**Timeline Component:**
```typescript
// src/components/DualView/TimelineView.tsx

interface TimelineViewProps {
  conversationId: string;
  height: string;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  zoomLevel: ZoomLevel;
  onZoomChange: (level: ZoomLevel) => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  conversationId,
  selectedNodeId,
  onSelectNode,
  zoomLevel
}) => {
  const { data: utterances } = useUtterances(conversationId);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Calculate marker positions based on timestamps
  const markers = useMemo(() => {
    return utterances.map((utt, idx) => ({
      id: utt.id,
      position: (utt.start_time / totalDuration) * 100, // Percentage
      speaker: utt.speaker,
      text: utt.text.substring(0, 50) + "..."
    }));
  }, [utterances]);

  // Render timeline
  return (
    <div className="timeline-view" ref={timelineRef}>
      <TimelineControls zoomLevel={zoomLevel} onZoomChange={onZoomChange} />

      <svg className="timeline-svg" width="100%" height="80">
        {/* Timeline axis */}
        <line x1="0" y1="40" x2="100%" y2="40" stroke="gray" strokeWidth="2" />

        {/* Node markers */}
        {markers.map(marker => (
          <g key={marker.id}>
            <circle
              cx={`${marker.position}%`}
              cy="40"
              r={selectedNodeId === marker.id ? 8 : 5}
              fill={getSpeakerColor(marker.speaker)}
              className="cursor-pointer hover:scale-110"
              onClick={() => onSelectNode(marker.id)}
            />
            <text
              x={`${marker.position}%`}
              y="60"
              fontSize="10"
              textAnchor="middle"
            >
              {marker.speaker}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};
```

**Timeline Zoom Levels:**
```typescript
enum TimelineGranularity {
  UTTERANCE = "utterance",  // Show every speaker turn
  TURN = "turn",            // Aggregate consecutive turns by same speaker
  TOPIC = "topic",          // Show topic boundaries only
  THEME = "theme"           // Show major themes/milestones
}

function filterMarkersByZoom(
  markers: TimelineMarker[],
  zoom: TimelineGranularity
): TimelineMarker[] {
  switch (zoom) {
    case TimelineGranularity.UTTERANCE:
      return markers; // All visible

    case TimelineGranularity.TURN:
      // Group consecutive same-speaker turns
      return aggregateTurns(markers);

    case TimelineGranularity.TOPIC:
      // Only show nodes marked as topic boundaries
      return markers.filter(m => m.isTopicBoundary);

    case TimelineGranularity.THEME:
      // Only major themes
      return markers.filter(m => m.isThemeBoundary);
  }
}
```

### Phase 3: Contextual Network View (Week 6, Days 1-3)

**Network Component:**
```typescript
// src/components/DualView/ContextualNetworkView.tsx

interface ContextualNetworkViewProps {
  conversationId: string;
  height: string;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  zoomLevel: ZoomLevel;
}

export const ContextualNetworkView: React.FC<ContextualNetworkViewProps> = ({
  conversationId,
  selectedNodeId,
  onSelectNode,
  zoomLevel
}) => {
  const { data: graphData } = useConversationGraph(conversationId);

  // Filter nodes based on zoom level
  const visibleNodes = useMemo(() => {
    return graphData.nodes.filter(node =>
      node.zoom_level_visible <= zoomLevel || node.pinned
    );
  }, [graphData, zoomLevel]);

  return (
    <div className="contextual-network-view">
      <NetworkControls />

      <ReactFlow
        nodes={visibleNodes.map(node => ({
          id: node.id,
          data: { label: node.summary, ...node },
          position: node.position,
          className: selectedNodeId === node.id ? "selected" : ""
        }))}
        edges={graphData.edges.map(edge => ({
          id: edge.id,
          source: edge.from_node_id,
          target: edge.to_node_id,
          type: edge.relationship_type === "temporal" ? "default" : "dashed",
          label: edge.label
        }))}
        onNodeClick={(event, node) => onSelectNode(node.id)}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
```

### Phase 4: Synchronization Logic (Week 6, Days 4-5)

**Shared State Management:**
```typescript
// src/hooks/useDualViewSync.ts

export const useDualViewSync = (conversationId: string) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>(3);
  const [timelinePosition, setTimelinePosition] = useState<number>(0);

  // When node selected, update timeline position
  useEffect(() => {
    if (selectedNodeId) {
      const node = getNodeById(selectedNodeId);
      if (node?.timestamp) {
        setTimelinePosition(node.timestamp);
      }
    }
  }, [selectedNodeId]);

  // When timeline position changes, highlight corresponding node
  useEffect(() => {
    const nodeAtTime = findNodeAtTimestamp(timelinePosition);
    if (nodeAtTime) {
      setSelectedNodeId(nodeAtTime.id);
    }
  }, [timelinePosition]);

  return {
    selectedNodeId,
    setSelectedNodeId,
    zoomLevel,
    setZoomLevel,
    timelinePosition,
    setTimelinePosition
  };
};
```

**Event Bus for Cross-View Communication:**
```typescript
// src/lib/viewSyncBus.ts

type ViewEvent =
  | { type: "NODE_SELECTED"; nodeId: string }
  | { type: "TIMELINE_POSITION_CHANGED"; timestamp: number }
  | { type: "ZOOM_LEVEL_CHANGED"; level: ZoomLevel };

class ViewSyncBus {
  private listeners: Set<(event: ViewEvent) => void> = new Set();

  emit(event: ViewEvent) {
    this.listeners.forEach(listener => listener(event));
  }

  subscribe(listener: (event: ViewEvent) => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export const viewSyncBus = new ViewSyncBus();
```

## Responsive Design & Accessibility

### Mobile/Tablet Adaptation

**Small Screens (< 768px):**
- Switch to tab-based view (user chooses one at a time)
- Floating timeline mini-map overlay

**Medium Screens (768px - 1024px):**
- Vertical split maintained
- Timeline collapses to mini-mode (icons only)
- Expand on hover

**Large Screens (> 1024px):**
- Full dual-view (default behavior)
- Optional side-by-side horizontal layout

### Keyboard Navigation

| Shortcut         | Action                              |
|------------------|-------------------------------------|
| `Tab`            | Cycle through nodes in timeline     |
| `Shift+Tab`      | Reverse cycle                       |
| `Arrow Keys`     | Navigate timeline left/right        |
| `Space`          | Play/pause timeline animation       |
| `Enter`          | Select node and focus in network    |
| `Esc`            | Clear selection                     |
| `+/-`            | Zoom in/out timeline                |
| `[/]`            | Adjust divider position             |

### Screen Reader Support

```typescript
// Accessibility attributes
<TimelineMarker
  role="button"
  aria-label={`${node.speaker} at ${formatTime(node.timestamp)}: ${node.summary}`}
  aria-selected={selectedNodeId === node.id}
  tabIndex={0}
  onKeyPress={(e) => e.key === "Enter" && onSelectNode(node.id)}
/>

<NetworkNode
  role="treeitem"
  aria-label={`Node: ${node.name}. Level: ${node.level}. ${node.children_ids.length} children.`}
  aria-expanded={node.isExpanded}
/>
```

## Performance Considerations

### Rendering Optimization

**Timeline View:**
- Use SVG viewBox for efficient scaling
- Canvas fallback for 1000+ markers
- Virtual scrolling for long conversations

**Network View:**
- React Flow's built-in viewport culling
- Only render visible nodes + 1-hop neighbors
- Memoize node/edge calculations

**Synchronization:**
- Debounce timeline scrubbing (50ms)
- Throttle network updates (100ms)
- Use requestAnimationFrame for animations

**Performance Budgets:**
- Initial render: < 200ms
- View switch: < 50ms
- Scroll/scrub: 60 FPS
- Memory: < 300MB for 500 nodes

### Code Splitting

```typescript
// Lazy load views
const ContextualNetworkView = lazy(() => import("./ContextualNetworkView"));
const TimelineView = lazy(() => import("./TimelineView"));

<Suspense fallback={<LoadingSpinner />}>
  <ContextualNetworkView {...props} />
  <TimelineView {...props} />
</Suspense>
```

## Testing Strategy

### Unit Tests

```typescript
// tests/DualViewCanvas.test.tsx

describe("DualViewCanvas", () => {
  it("renders both views with correct proportions", () => {
    render(<DualViewCanvas conversationId="test-123" />);

    const contextualView = screen.getByTestId("contextual-view");
    const timelineView = screen.getByTestId("timeline-view");

    expect(contextualView).toHaveStyle({ height: "85%" });
    expect(timelineView).toHaveStyle({ height: "15%" });
  });

  it("synchronizes node selection across views", () => {
    render(<DualViewCanvas conversationId="test-123" />);

    const timelineMarker = screen.getByLabelText("Node 1");
    fireEvent.click(timelineMarker);

    const networkNode = screen.getByTestId("network-node-1");
    expect(networkNode).toHaveClass("selected");
  });

  it("adjusts divider position on drag", () => {
    render(<DualViewCanvas conversationId="test-123" />);

    const divider = screen.getByTestId("resizable-divider");
    fireEvent.mouseDown(divider, { clientY: 500 });
    fireEvent.mouseMove(document, { clientY: 600 });
    fireEvent.mouseUp(document);

    const contextualView = screen.getByTestId("contextual-view");
    expect(contextualView).toHaveStyle({ height: expect.stringContaining("75") });
  });
});
```

### Integration Tests

```typescript
// tests/integration/dual-view-sync.test.tsx

describe("Dual View Synchronization", () => {
  it("updates timeline position when node selected in network", async () => {
    const { user } = setup(<DualViewCanvas conversationId="test-123" />);

    // Select node in network view
    const networkNode = screen.getByTestId("network-node-5");
    await user.click(networkNode);

    // Check timeline highlights corresponding marker
    const timelineMarker = screen.getByTestId("timeline-marker-5");
    expect(timelineMarker).toHaveClass("highlighted");
  });

  it("expands cluster in network when zooming timeline", async () => {
    const { user } = setup(<DualViewCanvas conversationId="test-123" />);

    // Zoom in timeline
    const zoomSlider = screen.getByLabelText("Zoom");
    await user.drag(zoomSlider, { x: 50 });

    // Check network view shows more nodes
    const visibleNodes = screen.getAllByTestId(/network-node-/);
    expect(visibleNodes.length).toBeGreaterThan(10);
  });
});
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/dual-view.spec.ts

test("dual view workflow", async ({ page }) => {
  await page.goto("/conversations/test-123");

  // Verify both views visible
  await expect(page.locator("[data-testid='contextual-view']")).toBeVisible();
  await expect(page.locator("[data-testid='timeline-view']")).toBeVisible();

  // Click timeline marker
  await page.click("[data-testid='timeline-marker-3']");

  // Verify network view centers on node
  const networkNode = page.locator("[data-testid='network-node-3']");
  await expect(networkNode).toHaveClass(/selected/);

  // Resize divider
  const divider = page.locator("[data-testid='resizable-divider']");
  await divider.hover();
  await page.mouse.down();
  await page.mouse.move(0, 100);
  await page.mouse.up();

  // Verify new proportions
  const timelineHeight = await page.locator("[data-testid='timeline-view']").evaluate(
    (el) => el.offsetHeight
  );
  expect(timelineHeight).toBeGreaterThan(150); // Resized larger
});
```

## Migration Path

### Backward Compatibility

**Existing Conversations:**
- Automatically split single view into dual view
- Preserve all node positions for contextual view
- Generate timeline markers from utterance timestamps

**User Preferences:**
- Detect existing users, offer opt-in tour
- Save divider position per user
- Allow "classic single view" toggle (deprecated)

**API Changes:**
- No breaking changes to backend APIs
- Frontend-only enhancement

## Success Metrics

**Usability:**
- Time to locate specific node: < 10 seconds (vs. 30s before)
- User satisfaction: 4.5/5 stars
- Feature adoption: 80% of users use both views

**Performance:**
- Initial render: < 200ms
- View sync latency: < 50ms
- 60 FPS during interaction

**Engagement:**
- Increased session duration: +25%
- More nodes explored per session: +40%
- Reduced "back" navigation: -50%

## Alternatives Considered

### Alternative A: Tabbed Views
- **Pro**: Simpler implementation
- **Con**: Breaks spatial context, requires mental effort to switch

### Alternative B: Picture-in-Picture
- **Pro**: Always visible context
- **Con**: Small PiP window hard to interact with

### Alternative C: Horizontal Split (Side-by-Side)
- **Pro**: Equal visual weight
- **Con**: Wastes horizontal space, network graph needs square area

### Alternative D: Overlaid Timeline
- **Pro**: Maximizes graph space
- **Con**: Occludes graph, hard to interact with both simultaneously

## Future Enhancements

1. **Miniature Network in Timeline**: Show micro-graph at each timeline marker
2. **3D Mode**: Timeline as Z-axis, network in XY plane
3. **Timeline Heatmap**: Color-code timeline by activity, sentiment, speaker
4. **Drag Node to Timeline**: Manually adjust node timestamp
5. **Timeline Filtering**: Show/hide speakers, topics directly in timeline
6. **Synchronized Playback**: Auto-play through conversation with visual animations

## References

- [Dual-View Visualization Patterns](https://www.researchgate.net/publication/221515790_Multiple_Coordinated_Views)
- [Timeline Design Best Practices](https://www.nngroup.com/articles/timeline-design/)
- [React Flow Documentation](https://reactflow.dev/)
- [Observable Plot Timeline Examples](https://observablehq.com/@d3/timeline)
- [Temporal + Network Visualization Research](https://ieeexplore.ieee.org/document/8019843)

---

**Decision Status**: Approved for implementation in Week 5-6 of roadmap.
