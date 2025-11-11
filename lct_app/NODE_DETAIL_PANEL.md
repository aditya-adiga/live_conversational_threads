# Node Detail Panel (Week 7)

## Overview

The **Node Detail Panel** is a slide-in detail view that appears when a node is selected in the visualization. It provides a split-screen interface showing the selected node's content along with zoom-dependent contextual information from surrounding nodes.

### Key Features

1. **Split-Screen Layout**: Three-section vertical layout showing previous context, current node, and next context
2. **Zoom-Dependent Context Loading**: Amount and detail of context adapts based on current zoom level
3. **Inline Editing**: Edit node title, summary, and keywords with validation
4. **Intentional Friction**: Explicit edit mode toggle prevents accidental changes
5. **Immediate Save**: Changes persist to backend immediately with diff tracking
6. **Smooth Animations**: 300ms slide-in/out transitions
7. **Temporal Navigation**: Shows previous/next nodes based on conversation flow

---

## Architecture

### Component Structure

```
NodeDetailPanel/
├── NodeDetailPanel.jsx       # Main panel component (300+ lines)
├── index.js                   # Export wrapper
```

### Utility Files

```
utils/
└── contextLoading.js          # Context loading utilities (200+ lines)
```

### Integration Point

```
DualView/
└── DualViewCanvas.jsx         # Hosts the slide-in panel
```

---

## Context Loading System

### Zoom-Dependent Configuration

The panel loads different amounts of context based on the current zoom level:

| Zoom Level | Previous Nodes | Next Nodes | Mode | Utterances | Summary | Keywords |
|------------|---------------|------------|------|------------|---------|----------|
| **1: SENTENCE** | 2 | 2 | detailed | ✅ | ✅ | ✅ |
| **2: TURN** | 1 | 1 | focused | ✅ | ✅ | ❌ |
| **3: TOPIC** | 1 | 1 | balanced | ❌ | ✅ | ✅ |
| **4: THEME** | 0 | 0 | summary | ❌ | ✅ | ✅ |
| **5: ARC** | 0 | 0 | overview | ❌ | ✅ | ❌ |

### Context Loading Algorithm

The system uses temporal edges to find previous/next nodes in conversation flow:

```javascript
// Build adjacency map from temporal edges
const temporalEdges = edges.filter(e => e.data?.edgeType === 'temporal');
const adjacency = {
  next: new Map(),    // node -> next node
  previous: new Map() // node -> previous node
};

temporalEdges.forEach(edge => {
  adjacency.next.set(edge.source, edge.target);
  adjacency.previous.set(edge.target, edge.source);
});

// Walk backward/forward from selected node
let current = selectedNode.id;
for (let i = 0; i < config.previousCount; i++) {
  current = adjacency.previous.get(current);
  if (current) previousNodes.push(allNodes.find(n => n.id === current));
}
```

### API Reference

#### `getContextConfig(zoomLevel)`

Returns configuration object for the given zoom level.

**Parameters:**
- `zoomLevel` (number): Current zoom level (1-5)

**Returns:**
```javascript
{
  previousCount: number,      // Number of previous nodes to load
  nextCount: number,          // Number of next nodes to load
  mode: string,               // Context mode name
  showUtterances: boolean,    // Whether to show raw utterances
  showSummary: boolean,       // Whether to show summary
  showKeywords: boolean       // Whether to show keywords
}
```

**Example:**
```javascript
import { getContextConfig } from '../utils/contextLoading';

const config = getContextConfig(3); // Topic level
// Returns: { previousCount: 1, nextCount: 1, mode: 'balanced', ... }
```

---

#### `getContextNodes(selectedNode, allNodes, edges, zoomLevel)`

Retrieves previous and next context nodes based on temporal edges.

**Parameters:**
- `selectedNode` (object): Currently selected ReactFlow node
- `allNodes` (array): All nodes in the graph
- `edges` (array): All edges in the graph
- `zoomLevel` (number): Current zoom level (1-5)

**Returns:**
```javascript
{
  previous: Node[],     // Previous context nodes (ordered oldest to newest)
  current: Node,        // Selected node
  next: Node[],         // Next context nodes (ordered chronologically)
  config: Object        // Context configuration used
}
```

**Example:**
```javascript
import { getContextNodes } from '../utils/contextLoading';

const contextData = getContextNodes(selectedNode, allNodes, edges, 2);
// At Turn level: { previous: [node1], current: selectedNode, next: [node2], config: {...} }
```

---

#### `validateNodeEdits(originalNode, editedNode)`

Validates edited node data before saving.

**Parameters:**
- `originalNode` (object): Original node data
- `editedNode` (object): Edited node data with changes

**Returns:**
```javascript
{
  valid: boolean,       // Whether validation passed
  errors: string[]      // Array of error messages
}
```

**Validation Rules:**
- Title cannot be empty
- Title must be ≤ 200 characters
- Summary must be ≤ 2000 characters
- Maximum 20 keywords allowed

**Example:**
```javascript
import { validateNodeEdits } from '../utils/contextLoading';

const validation = validateNodeEdits(originalNode, editedNode);
if (!validation.valid) {
  console.error('Validation failed:', validation.errors);
}
```

---

#### `getNodeDiff(originalNode, editedNode)`

Calculates differences between original and edited node data.

**Parameters:**
- `originalNode` (object): Original node data
- `editedNode` (object): Edited node data

**Returns:**
```javascript
{
  title?: { old: string, new: string },
  summary?: { old: string, new: string },
  keywords?: { old: string[], new: string[] }
}
```

**Example:**
```javascript
import { getNodeDiff } from '../utils/contextLoading';

const diff = getNodeDiff(originalNode, editedNode);
// Returns: { title: { old: 'Old Title', new: 'New Title' } }
```

---

## NodeDetailPanel Component

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `selectedNode` | object | ✅ | Currently selected ReactFlow node |
| `allNodes` | array | ✅ | All nodes in the graph |
| `edges` | array | ✅ | All edges in the graph |
| `zoomLevel` | number | ✅ | Current zoom level (1-5) |
| `onClose` | function | ✅ | Callback when panel is closed |
| `onSave` | function | ✅ | Callback when node is saved: `(nodeId, updatedNode, diff) => Promise` |
| `utterancesMap` | object | ❌ | Map of node ID to utterances array (future use) |

### State Management

```javascript
const [isEditMode, setIsEditMode] = useState(false);
const [editedNode, setEditedNode] = useState(null);
const [isSaving, setIsSaving] = useState(false);
const [saveError, setSaveError] = useState(null);
const [validationErrors, setValidationErrors] = useState([]);
```

### User Interactions

#### Viewing Mode (Default)
- **Close Panel**: Click X button or press ESC
- **Enter Edit Mode**: Click "Edit Node" button
- **View Context**: Scroll to see previous/next nodes

#### Edit Mode
- **Edit Title**: Click title input, type changes
- **Edit Summary**: Click summary textarea, type changes
- **Edit Keywords**: Add/remove keyword tags
- **Cancel Changes**: Click "Cancel" button
- **Save Changes**: Click "Save Changes" button
- **Validation**: Errors appear above save buttons

### Visual States

#### Panel Position
```javascript
// Slide in from right when node selected
className={`absolute top-0 right-0 h-full w-96 transform transition-transform duration-300 ease-in-out z-50 ${
  showDetailPanel ? 'translate-x-0' : 'translate-x-full'
}`}
```

#### Edit Mode Indicator
```javascript
// Blue border when in edit mode
className={`rounded-lg ${isEditMode ? 'border-2 border-blue-500' : 'border border-gray-300'}`}
```

---

## Integration Guide

### 1. Import Components and Utilities

```javascript
import { NodeDetailPanel } from '../components/NodeDetailPanel';
import { saveNode } from '../services/graphApi';
```

### 2. Add State Management

```javascript
const [showDetailPanel, setShowDetailPanel] = useState(false);

// Show/hide panel when node is selected/deselected
useEffect(() => {
  setShowDetailPanel(!!zoomController.selectedNode);
}, [zoomController.selectedNode]);
```

### 3. Implement Save Handler

```javascript
const handleSaveNode = async (nodeId, updatedNode, diff) => {
  try {
    await saveNode(nodeId, updatedNode, diff);
    // Reload graph data to reflect changes
    const data = await fetchGraph(conversationId, null, true);
    setGraphData(data);
  } catch (error) {
    console.error('Failed to save node:', error);
    throw error; // Re-throw to let NodeDetailPanel handle it
  }
};
```

### 4. Render Panel

```javascript
<div
  className={`absolute top-0 right-0 h-full w-96 transform transition-transform duration-300 ease-in-out z-50 ${
    showDetailPanel ? 'translate-x-0' : 'translate-x-full'
  }`}
>
  {showDetailPanel && zoomController.selectedNode && (
    <NodeDetailPanel
      selectedNode={nodes.find(n => n.id === zoomController.selectedNode)}
      allNodes={nodes}
      edges={edges}
      zoomLevel={zoomController.zoomLevel}
      onClose={() => zoomController.setSelectedNode(null)}
      onSave={handleSaveNode}
      utterancesMap={{}}
    />
  )}
</div>
```

---

## Backend Integration

### Save Node API Endpoint

**Request:**
```
PUT /api/nodes/{nodeId}
Content-Type: application/json

{
  "title": "Updated Title",
  "summary": "Updated summary text...",
  "keywords": ["keyword1", "keyword2"],
  "changes": {
    "title": { "old": "Old Title", "new": "Updated Title" },
    "summary": { "old": "Old summary...", "new": "Updated summary..." }
  }
}
```

**Response:**
```json
{
  "success": true,
  "node": {
    "id": "node_123",
    "title": "Updated Title",
    "summary": "Updated summary text...",
    "keywords": ["keyword1", "keyword2"]
  }
}
```

**Error Response:**
```json
{
  "detail": "Validation failed: Title cannot be empty"
}
```

### API Client Function

```javascript
// src/services/graphApi.js
export async function saveNode(nodeId, updatedNode, diff) {
  const url = `${API_BASE_URL}/api/nodes/${nodeId}`;

  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: updatedNode.title,
      summary: updatedNode.summary,
      keywords: updatedNode.keywords,
      changes: diff,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to save node: ${response.statusText}`);
  }

  return await response.json();
}
```

---

## Keyboard Shortcuts

| Key | Action | Mode |
|-----|--------|------|
| **ESC** | Close panel / Cancel edit | Any |
| **Ctrl+E** | Enter edit mode | View mode (future) |
| **Ctrl+S** | Save changes | Edit mode (future) |

---

## Styling and Layout

### Panel Dimensions
- **Width**: 24rem (w-96 / 384px)
- **Height**: 100vh (full screen height)
- **Position**: Fixed to right edge
- **Z-index**: 50 (overlays everything)

### Section Layout
```
┌─────────────────────────────┐
│ PREVIOUS CONTEXT            │  ← Collapsed by default
│ (Expandable section)        │
├─────────────────────────────┤
│                             │
│ CURRENT NODE                │  ← Always expanded
│ Title, Summary, Keywords    │
│ [Edit Mode UI]              │
│                             │
├─────────────────────────────┤
│ NEXT CONTEXT                │  ← Collapsed by default
│ (Expandable section)        │
└─────────────────────────────┘
```

### Color Scheme
- **Background**: white (`bg-white`)
- **Border**: gray-300 (`border-gray-300`)
- **Edit Mode Border**: blue-500 (`border-blue-500`)
- **Header**: blue-600 (`bg-blue-600`)
- **Context Sections**: gray-50 (`bg-gray-50`)
- **Buttons**: blue-600, gray-300 (primary, secondary)

---

## Performance Considerations

### Context Loading Optimization

```javascript
// Use useMemo to avoid recalculating context on every render
const contextData = useMemo(() => {
  if (!selectedNode) return null;
  return getContextNodes(selectedNode, allNodes, edges, zoomLevel);
}, [selectedNode, allNodes, edges, zoomLevel]);
```

### Lazy Rendering

```javascript
// Only render panel when visible
{showDetailPanel && zoomController.selectedNode && (
  <NodeDetailPanel {...props} />
)}
```

### Transition Performance

```css
/* Use GPU-accelerated transforms instead of left/right positioning */
transform: translateX(0);      /* Visible */
transform: translateX(100%);   /* Hidden */
transition: transform 300ms ease-in-out;
```

---

## Edit Mode Workflow

### 1. Enter Edit Mode

```
User clicks "Edit Node" button
  ↓
isEditMode = true
  ↓
editedNode = copy of selectedNode data
  ↓
Input fields become editable
  ↓
Cancel/Save buttons appear
```

### 2. Make Changes

```
User types in title input
  ↓
setEditedNode({ ...editedNode, title: newValue })
  ↓
User adds keyword tag
  ↓
setEditedNode({ ...editedNode, keywords: [...keywords, newKeyword] })
```

### 3. Save Changes

```
User clicks "Save Changes"
  ↓
validateNodeEdits(originalNode, editedNode)
  ↓
If invalid: show validation errors, stop
  ↓
getNodeDiff(originalNode, editedNode)
  ↓
If no changes: exit edit mode, stop
  ↓
Call onSave(nodeId, editedNode, diff)
  ↓
Backend saves changes
  ↓
Reload graph data
  ↓
Exit edit mode
```

### 4. Cancel Changes

```
User clicks "Cancel" or presses ESC
  ↓
editedNode = null
  ↓
isEditMode = false
  ↓
validationErrors = []
  ↓
Return to view mode
```

---

## Error Handling

### Validation Errors

Displayed above save buttons in edit mode:

```javascript
{validationErrors.length > 0 && (
  <div className="bg-red-50 border border-red-300 rounded-lg p-3 mb-3">
    <ul className="text-sm text-red-700 space-y-1">
      {validationErrors.map((error, i) => (
        <li key={i}>• {error}</li>
      ))}
    </ul>
  </div>
)}
```

### Save Errors

Displayed above save buttons after failed save:

```javascript
{saveError && (
  <div className="bg-red-50 border border-red-300 rounded-lg p-3 mb-3">
    <p className="text-sm text-red-700">{saveError}</p>
  </div>
)}
```

### Network Errors

Caught in handleSave and re-thrown to panel:

```javascript
try {
  await onSave(selectedNode.id, editedNode, diff);
  setIsEditMode(false);
} catch (error) {
  setSaveError(error.message);
} finally {
  setIsSaving(false);
}
```

---

## Testing Checklist

### Context Loading Tests
- [ ] Level 1: Loads 2 previous + 2 next nodes
- [ ] Level 2: Loads 1 previous + 1 next node
- [ ] Level 3: Loads 1 previous + 1 next node
- [ ] Level 4-5: Loads 0 context nodes
- [ ] Empty context handled gracefully
- [ ] Temporal edges correctly followed

### Edit Mode Tests
- [ ] Edit button enters edit mode
- [ ] Cancel button exits without saving
- [ ] ESC key exits without saving
- [ ] Save button validates before saving
- [ ] Empty title shows validation error
- [ ] Long title (>200 chars) shows error
- [ ] Long summary (>2000 chars) shows error
- [ ] Too many keywords (>20) shows error
- [ ] Valid changes save successfully
- [ ] No changes skips save

### Integration Tests
- [ ] Panel slides in when node selected
- [ ] Panel slides out when node deselected
- [ ] Panel slides out when closed manually
- [ ] Save reloads graph data
- [ ] Saved changes appear in graph
- [ ] Selected node remains selected after save

### Edge Cases
- [ ] Node with no previous neighbors
- [ ] Node with no next neighbors
- [ ] Node at start of conversation
- [ ] Node at end of conversation
- [ ] Network error during save
- [ ] Backend validation error

---

## Troubleshooting

### Panel Not Appearing

**Symptom**: Panel doesn't slide in when node selected

**Check:**
1. `showDetailPanel` state is true
2. `zoomController.selectedNode` has value
3. Z-index (50) is higher than other elements
4. Transform classes correctly applied

**Fix:**
```javascript
console.log('showDetailPanel:', showDetailPanel);
console.log('selectedNode:', zoomController.selectedNode);
console.log('Found node:', nodes.find(n => n.id === zoomController.selectedNode));
```

---

### Context Nodes Not Loading

**Symptom**: Previous/next sections empty or show wrong nodes

**Check:**
1. Temporal edges exist in graph
2. Edge `data.edgeType === 'temporal'`
3. Adjacency map correctly built
4. Zoom level configuration correct

**Fix:**
```javascript
const temporalEdges = edges.filter(e => e.data?.edgeType === 'temporal');
console.log('Temporal edges:', temporalEdges.length);
console.log('Config:', getContextConfig(zoomLevel));
```

---

### Save Not Working

**Symptom**: Changes don't persist to backend

**Check:**
1. `onSave` prop correctly passed
2. Backend endpoint `/api/nodes/{nodeId}` exists
3. Network request succeeds
4. Graph reload occurs after save

**Fix:**
```javascript
const handleSaveNode = async (nodeId, updatedNode, diff) => {
  console.log('Saving:', nodeId, updatedNode, diff);
  try {
    const result = await saveNode(nodeId, updatedNode, diff);
    console.log('Save result:', result);
    // ... reload graph
  } catch (error) {
    console.error('Save error:', error);
  }
};
```

---

### Validation Errors Persisting

**Symptom**: Validation errors don't clear after fixing

**Check:**
1. `setValidationErrors([])` called before validation
2. State updates correctly on input change

**Fix:**
```javascript
const handleSave = async () => {
  setValidationErrors([]); // Clear previous errors
  setSaveError(null);      // Clear previous save errors

  const validation = validateNodeEdits(selectedNode, editedNode);
  // ... rest of save logic
};
```

---

## Future Enhancements

### Phase 1 (Week 8)
- [ ] Show speaker attribution in context nodes
- [ ] Filter context by speaker
- [ ] Highlight speaker changes in timeline

### Phase 2 (Week 9)
- [ ] Link to prompts used for node generation
- [ ] Show confidence scores
- [ ] Regenerate node with different prompt

### Phase 3 (Week 10)
- [ ] Show edit history timeline
- [ ] Diff viewer for changes
- [ ] Rollback to previous version
- [ ] Export edited nodes as training data

### Phase 4 (Future)
- [ ] Keyboard shortcut support (Ctrl+E, Ctrl+S)
- [ ] Rich text editor for summary
- [ ] Tag autocomplete for keywords
- [ ] Drag-to-reorder keywords
- [ ] Utterance timestamps and playback
- [ ] Audio snippet playback
- [ ] Comment/annotation system
- [ ] Collaborative editing (multi-user)

---

## Related Documentation

- [DUAL_VIEW_ARCHITECTURE.md](./DUAL_VIEW_ARCHITECTURE.md) - Dual-view system overview
- [ZOOM_SYSTEM.md](./ZOOM_SYSTEM.md) - 5-level zoom system details
- [ROADMAP.md](./ROADMAP.md) - Overall project roadmap
- [GRAPH_API.md](./GRAPH_API.md) - Backend API reference (Week 4)

---

## Summary

The Node Detail Panel provides an intuitive interface for viewing and editing individual nodes with appropriate contextual information based on the current zoom level. Key design principles:

1. **Intentional Friction**: Explicit edit mode prevents accidental changes
2. **Context Awareness**: Zoom level determines context depth
3. **Immediate Feedback**: Validation and save errors appear inline
4. **Smooth UX**: 300ms animations for all transitions
5. **Backend Integration**: Changes persist with diff tracking for edit history

This completes Week 7 of the Live Conversational Threads V2 roadmap.
