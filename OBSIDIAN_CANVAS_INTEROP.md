# Obsidian Canvas Interoperability

This feature enables bidirectional conversion between Live Conversational Threads and [Obsidian Canvas](https://obsidian.md/) format, allowing you to visualize and edit conversation trees in Obsidian or other Canvas-compatible applications.

## Features

### Export to Obsidian Canvas
Convert your conversation trees into Obsidian Canvas format (`.canvas` files) that can be opened in Obsidian.

**What gets exported:**
- **Conversation nodes** → Canvas text nodes with markdown content
- **Node summaries** → Formatted markdown text
- **Claims** → Bulleted lists in markdown
- **Temporal relationships** (predecessor/successor) → Red edges labeled "next"
- **Contextual relationships** → Yellow edges with relationship explanations
- **Bookmarks** → Cyan/blue colored nodes (color "5")
- **Contextual Progress** → Green colored nodes (color "4")
- **Optional: Chunk content** → Purple nodes linked to conversation nodes

**Layout:**
- Nodes are automatically positioned using a hierarchical layout algorithm
- Temporal flow is left-to-right
- Contextual relationships branch out from the main flow

### Import from Obsidian Canvas
Import Canvas files and convert them back into conversation tree format.

**What gets imported:**
- **Canvas text nodes** → Conversation nodes
- **Node text** → Parsed into summary, claims, and metadata
- **Red edges / "next" labels** → Temporal relationships
- **Other edges** → Contextual relationships
- **Node colors** → Bookmark and contextual progress flags
- **Optional: Preserve positions** → Store original Canvas coordinates for future use

## Usage

### Exporting a Conversation

1. **From the View Conversation page:**
   - Open a saved conversation
   - Click the "Export to Canvas" button (purple button in the header)
   - Optional: Check "Include chunks" to export transcript chunks as separate nodes
   - The `.canvas` file will be downloaded automatically

2. **API endpoint:**
   ```bash
   POST /export/obsidian-canvas/{conversation_id}?include_chunks=false
   ```

3. **Opening in Obsidian:**
   - Save the downloaded `.canvas` file to your Obsidian vault
   - Open it in Obsidian to view and edit the conversation tree

### Importing a Canvas File

1. **From the Browse page:**
   - Click the "Import from Canvas" button (indigo button in the header)
   - Select a `.canvas` file from your file system
   - Optional: Enter a custom name for the imported conversation
   - The conversation will be imported and you'll be redirected to the view page

2. **API endpoint:**
   ```bash
   POST /import/obsidian-canvas/
   Content-Type: application/json

   {
     "canvas_data": { ... },
     "file_name": "Imported Conversation",
     "preserve_positions": true
   }
   ```

## Technical Details

### Canvas Format Mapping

#### Node Mapping
| Conversation Field | Canvas Field | Notes |
|-------------------|--------------|-------|
| `node_name` | `id` (sanitized) | Spaces replaced with underscores |
| `summary` | `text` | Formatted as markdown |
| `is_bookmark` | `color: "5"` | Cyan/blue color |
| `is_contextual_progress` | `color: "4"` | Green color |
| `claims[]` | `text` (section) | Formatted as bullet list |
| Position (calculated) | `x, y` | Auto-layout algorithm |

#### Edge Mapping
| Relationship Type | Canvas Edge Properties | Notes |
|------------------|----------------------|-------|
| Temporal (successor) | `color: "1"`, `label: "next"` | Red arrows |
| Contextual | `color: "3"`, `label: <explanation>` | Yellow lines |
| Chunk reference | `color: "2"`, `label: "references"` | Orange lines |

### Layout Algorithm

The export uses a hierarchical layout:
- **Horizontal spacing**: 400px between nodes
- **Vertical spacing**: 250px between rows
- **Node width**: 350px
- **Node height**: Calculated based on text length (200-600px)

Nodes are positioned:
1. Find root nodes (no predecessors)
2. Recursively layout successors horizontally
3. Position orphan nodes below the main structure

### Color Scheme

Canvas uses preset colors (1-6) that map to application-specific colors:

| Number | Color | Usage |
|--------|-------|-------|
| "1" | Red | Temporal flow edges |
| "2" | Orange | Chunk reference edges |
| "3" | Yellow | Contextual relationship edges |
| "4" | Green | Contextual progress nodes |
| "5" | Cyan/Blue | Bookmark nodes |
| "6" | Purple | Chunk nodes |

## API Reference

### Export Endpoint

**POST** `/export/obsidian-canvas/{conversation_id}`

**Query Parameters:**
- `include_chunks` (boolean, optional): Include transcript chunks as separate nodes. Default: `false`

**Response:**
```json
{
  "nodes": [
    {
      "id": "Node_Name",
      "type": "text",
      "x": 100,
      "y": 100,
      "width": 350,
      "height": 200,
      "color": "5",
      "text": "# Node Name\n\nSummary text..."
    }
  ],
  "edges": [
    {
      "id": "edge_0",
      "fromNode": "Node_1",
      "toNode": "Node_2",
      "fromSide": "right",
      "toSide": "left",
      "color": "1",
      "label": "next"
    }
  ]
}
```

### Import Endpoint

**POST** `/import/obsidian-canvas/`

**Request Body:**
```json
{
  "canvas_data": {
    "nodes": [...],
    "edges": [...]
  },
  "file_name": "My Conversation",
  "preserve_positions": true
}
```

**Response:**
```json
{
  "message": "Successfully imported Canvas as conversation",
  "file_id": "uuid-of-conversation",
  "file_name": "My Conversation"
}
```

## Limitations and Considerations

1. **Node IDs**: Canvas node IDs use underscores instead of spaces. Spaces are restored on import.

2. **Chunk References**: When not including chunks in export, chunk IDs are noted in node text but not linked.

3. **Metadata Loss**: Some internal metadata (like `claims_checked`, exact `chunk_id`) may not survive a full export/import roundtrip.

4. **Position Preservation**: Import can optionally preserve Canvas positions in `_canvas_metadata` field for future use.

5. **File Nodes**: Currently only text nodes are supported. File and link nodes in Canvas will be skipped on import.

6. **Edge Inference**: Import infers temporal vs contextual relationships based on edge colors and labels. Manual Canvas editing should follow these conventions.

## Examples

### Example 1: Simple Export
```javascript
// Frontend usage
const response = await fetch(
  `${API_URL}/export/obsidian-canvas/${conversationId}`,
  { method: 'POST' }
);
const canvasData = await response.json();

// Download file
const blob = new Blob([JSON.stringify(canvasData, null, 2)],
  { type: 'application/json' }
);
const url = URL.createObjectURL(blob);
// ... download logic
```

### Example 2: Import with Custom Name
```javascript
const response = await fetch(`${API_URL}/import/obsidian-canvas/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    canvas_data: canvasJsonData,
    file_name: 'Research Notes from Obsidian',
    preserve_positions: true
  })
});
```

## Future Enhancements

Potential improvements for future versions:

1. **Bidirectional Sync**: Real-time sync between LCT and Obsidian
2. **Custom Layouts**: Support for different layout algorithms (force-directed, circular, etc.)
3. **File Node Support**: Export chunks as markdown files instead of inline nodes
4. **Link Nodes**: Support for external URL references
5. **Group Nodes**: Support for grouping related conversation topics
6. **Metadata Preservation**: Store more internal metadata in Canvas custom fields
7. **Style Customization**: Allow users to customize colors, sizes, and layouts

## Troubleshooting

**Export fails with "Conversation not found":**
- Ensure the conversation ID is correct
- Check that the conversation exists in the database

**Import fails with "Invalid canvas file format":**
- Verify the file is valid JSON
- Ensure it follows the Obsidian Canvas spec (has `nodes` and `edges` arrays)
- Check that node IDs are unique

**Nodes appear in wrong positions:**
- The layout algorithm is deterministic but may produce unexpected results for complex graphs
- You can manually rearrange nodes in Obsidian and re-import with `preserve_positions: true`

**Missing relationships after import:**
- Check that edges have proper colors or labels
- Temporal edges should be red (color "1") or have label "next"
- Contextual edges should have labels or use other colors

## Resources

- [Obsidian Canvas Documentation](https://obsidian.md/canvas)
- [JSON Canvas Specification](https://jsoncanvas.org/)
- [Obsidian Forum: Creating Canvas Programmatically](https://forum.obsidian.md/t/creating-a-canvas-programmatically/101850/2)
