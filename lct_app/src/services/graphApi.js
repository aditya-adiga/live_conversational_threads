/**
 * API Client for Live Conversational Threads Graph Generation Service
 *
 * Connects to the FastAPI backend implemented in Week 4.
 * Handles fetching graph data, nodes, edges, and managing zoom levels.
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

/**
 * Fetch complete graph for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @param {number|null} zoomLevel - Optional zoom level filter (1-5)
 * @param {boolean} includeEdges - Whether to include edges (default: true)
 * @returns {Promise<Object>} Graph data with nodes and edges
 */
export async function fetchGraph(conversationId, zoomLevel = null, includeEdges = true) {
  const params = new URLSearchParams();
  if (zoomLevel !== null) {
    params.append('zoom_level', zoomLevel);
  }
  if (!includeEdges) {
    params.append('include_edges', 'false');
  }

  const url = `${API_BASE_URL}/api/graph/${conversationId}?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch graph: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetch only nodes for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @param {number|null} zoomLevel - Optional zoom level filter (1-5)
 * @returns {Promise<Object>} Nodes data
 */
export async function fetchNodes(conversationId, zoomLevel = null) {
  const params = new URLSearchParams();
  if (zoomLevel !== null) {
    params.append('zoom_level', zoomLevel);
  }

  const url = `${API_BASE_URL}/api/graph/${conversationId}/nodes?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch nodes: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetch only edges for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @param {string|null} relationshipType - Optional filter: "temporal" or "contextual"
 * @returns {Promise<Object>} Edges data
 */
export async function fetchEdges(conversationId, relationshipType = null) {
  const params = new URLSearchParams();
  if (relationshipType !== null) {
    params.append('relationship_type', relationshipType);
  }

  const url = `${API_BASE_URL}/api/graph/${conversationId}/edges?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch edges: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Generate graph from conversation transcript
 * @param {string} conversationId - UUID of the conversation
 * @param {boolean} useLLM - Whether to use LLM for generation (default: true)
 * @param {string} model - LLM model to use (default: "gpt-4")
 * @param {boolean} detectRelationships - Whether to detect contextual relationships (default: true)
 * @returns {Promise<Object>} Generation status
 */
export async function generateGraph(
  conversationId,
  useLLM = true,
  model = 'gpt-4',
  detectRelationships = true
) {
  const url = `${API_BASE_URL}/api/graph/generate`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      use_llm: useLLM,
      model: model,
      detect_relationships: detectRelationships,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate graph: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Delete graph for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @returns {Promise<Object>} Deletion status
 */
export async function deleteGraph(conversationId) {
  const url = `${API_BASE_URL}/api/graph/${conversationId}`;

  const response = await fetch(url, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete graph: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Transform backend node data to ReactFlow format
 * @param {Array} nodes - Array of nodes from backend
 * @param {number|null} currentZoomLevel - Current zoom level for filtering
 * @returns {Array} ReactFlow-formatted nodes
 */
export function transformNodesToReactFlow(nodes, currentZoomLevel = null) {
  return nodes
    .filter(node => {
      // Filter by zoom level if specified
      if (currentZoomLevel !== null) {
        return node.zoom_level_visible.includes(currentZoomLevel);
      }
      return true;
    })
    .map(node => ({
      id: node.id,
      type: 'default',
      data: {
        label: node.title,
        summary: node.summary,
        keywords: node.keywords,
        speakerInfo: node.speaker_info,
        utteranceIds: node.utterance_ids,
        zoomLevels: node.zoom_level_visible,
      },
      position: {
        x: node.canvas_x || 0,
        y: node.canvas_y || 0,
      },
      style: {
        background: 'white',
        border: '1px solid #ccc',
        borderRadius: '8px',
        padding: '10px',
        minWidth: '150px',
      },
    }));
}

/**
 * Transform backend edge data to ReactFlow format
 * @param {Array} edges - Array of edges from backend
 * @param {string|null} edgeTypeFilter - Filter by "temporal" or "contextual"
 * @returns {Array} ReactFlow-formatted edges
 */
export function transformEdgesToReactFlow(edges, edgeTypeFilter = null) {
  return edges
    .filter(edge => {
      if (edgeTypeFilter !== null) {
        return edge.relationship_type === edgeTypeFilter;
      }
      return true;
    })
    .map(edge => {
      const isTemporal = edge.relationship_type === 'temporal';

      return {
        id: edge.id,
        source: edge.source_node_id,
        target: edge.target_node_id,
        animated: !isTemporal, // Animate contextual edges
        type: 'default',
        data: {
          relationshipType: edge.relationship_type,
          strength: edge.strength,
          description: edge.description,
        },
        style: {
          stroke: isTemporal ? '#898989' : '#3b82f6', // Gray for temporal, blue for contextual
          strokeWidth: isTemporal ? 2 : 3,
          opacity: isTemporal ? 0.6 : 0.8,
        },
        markerEnd: {
          type: 'arrowclosed',
          width: 10,
          height: 10,
          color: isTemporal ? '#898989' : '#3b82f6',
        },
      };
    });
}

/**
 * Get zoom level name
 * @param {number} level - Zoom level (1-5)
 * @returns {string} Level name
 */
export function getZoomLevelName(level) {
  const names = {
    1: 'SENTENCE',
    2: 'TURN',
    3: 'TOPIC',
    4: 'THEME',
    5: 'ARC',
  };
  return names[level] || 'UNKNOWN';
}

/**
 * Calculate zoom level distribution
 * @param {Array} nodes - Array of nodes
 * @returns {Object} Distribution by zoom level
 */
export function calculateZoomDistribution(nodes) {
  const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };

  nodes.forEach(node => {
    node.zoom_level_visible.forEach(level => {
      distribution[level] = (distribution[level] || 0) + 1;
    });
  });

  return distribution;
}

/**
 * Save node changes to backend (Week 7)
 * @param {string} nodeId - Node UUID
 * @param {Object} updatedNode - Updated node data
 * @param {Object} diff - Object containing changed fields
 * @returns {Promise<Object>} Updated node data
 */
export async function saveNode(nodeId, updatedNode, diff) {
  const url = `${API_BASE_URL}/api/nodes/${nodeId}`;

  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: updatedNode.title,
      summary: updatedNode.summary,
      keywords: updatedNode.keywords,
      changes: diff, // Include diff for edit history logging
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to save node: ${response.statusText}`);
  }

  return await response.json();
}

export default {
  fetchGraph,
  fetchNodes,
  fetchEdges,
  generateGraph,
  deleteGraph,
  saveNode,
  transformNodesToReactFlow,
  transformEdgesToReactFlow,
  getZoomLevelName,
  calculateZoomDistribution,
};
