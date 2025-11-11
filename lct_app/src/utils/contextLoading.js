/**
 * Context Loading Utilities (Week 7)
 *
 * Zoom-dependent context loading for Node Detail Panel.
 * Determines how many surrounding nodes to show based on zoom level.
 */

/**
 * Get context configuration for a zoom level
 * @param {number} zoomLevel - Current zoom level (1-5)
 * @returns {Object} Context configuration
 */
export function getContextConfig(zoomLevel) {
  const configs = {
    1: {
      // SENTENCE: Show detailed surrounding context
      previousCount: 2,
      nextCount: 2,
      mode: 'detailed',
      showUtterances: true,
      showSummary: true,
      showKeywords: true,
    },
    2: {
      // TURN: Show focused context
      previousCount: 1,
      nextCount: 1,
      mode: 'focused',
      showUtterances: true,
      showSummary: true,
      showKeywords: false,
    },
    3: {
      // TOPIC: Balanced view
      previousCount: 1,
      nextCount: 1,
      mode: 'balanced',
      showUtterances: false,
      showSummary: true,
      showKeywords: true,
    },
    4: {
      // THEME: High-level context
      previousCount: 0,
      nextCount: 0,
      mode: 'summary',
      showUtterances: false,
      showSummary: true,
      showKeywords: true,
    },
    5: {
      // ARC: Summary of entire thread
      previousCount: 0,
      nextCount: 0,
      mode: 'overview',
      showUtterances: false,
      showSummary: true,
      showKeywords: false,
    },
  };

  return configs[zoomLevel] || configs[3]; // Default to TOPIC
}

/**
 * Get context nodes for a selected node
 * @param {Object} selectedNode - Selected node object
 * @param {Array} allNodes - All nodes in the graph
 * @param {Array} edges - All edges in the graph
 * @param {number} zoomLevel - Current zoom level
 * @returns {Object} Context nodes { previous, current, next }
 */
export function getContextNodes(selectedNode, allNodes, edges, zoomLevel) {
  if (!selectedNode) {
    return { previous: [], current: null, next: [] };
  }

  const config = getContextConfig(zoomLevel);

  // Find temporal edges to determine sequential order
  const temporalEdges = edges.filter(e => e.data?.relationshipType === 'temporal');

  // Build adjacency map
  const adjacencyMap = new Map();
  temporalEdges.forEach(edge => {
    if (!adjacencyMap.has(edge.source)) {
      adjacencyMap.set(edge.source, { prev: [], next: [] });
    }
    if (!adjacencyMap.has(edge.target)) {
      adjacencyMap.set(edge.target, { prev: [], next: [] });
    }
    adjacencyMap.get(edge.source).next.push(edge.target);
    adjacencyMap.get(edge.target).prev.push(edge.source);
  });

  const nodeMap = new Map(allNodes.map(n => [n.id, n]));

  // Get previous nodes
  const previousNodeIds = [];
  let currentId = selectedNode.id;
  for (let i = 0; i < config.previousCount; i++) {
    const adj = adjacencyMap.get(currentId);
    if (adj && adj.prev.length > 0) {
      const prevId = adj.prev[0]; // Take first previous
      previousNodeIds.unshift(prevId);
      currentId = prevId;
    } else {
      break;
    }
  }

  // Get next nodes
  const nextNodeIds = [];
  currentId = selectedNode.id;
  for (let i = 0; i < config.nextCount; i++) {
    const adj = adjacencyMap.get(currentId);
    if (adj && adj.next.length > 0) {
      const nextId = adj.next[0]; // Take first next
      nextNodeIds.push(nextId);
      currentId = nextId;
    } else {
      break;
    }
  }

  return {
    previous: previousNodeIds.map(id => nodeMap.get(id)).filter(Boolean),
    current: selectedNode,
    next: nextNodeIds.map(id => nodeMap.get(id)).filter(Boolean),
    config,
  };
}

/**
 * Format utterances for display
 * @param {Array} utteranceIds - Array of utterance IDs
 * @param {Object} utterancesMap - Map of utterance ID to utterance object
 * @returns {string} Formatted utterances text
 */
export function formatUtterances(utteranceIds, utterancesMap) {
  if (!utteranceIds || utteranceIds.length === 0) {
    return 'No utterances available';
  }

  return utteranceIds
    .map(id => {
      const utt = utterancesMap[id];
      if (!utt) return null;
      return `${utt.speaker}: ${utt.text}`;
    })
    .filter(Boolean)
    .join('\n\n');
}

/**
 * Get context description based on zoom level
 * @param {number} zoomLevel - Current zoom level
 * @returns {string} Description text
 */
export function getContextDescription(zoomLevel) {
  const descriptions = {
    1: 'Showing detailed context with full utterances from surrounding nodes',
    2: 'Showing immediate context with utterances from adjacent nodes',
    3: 'Showing balanced context with summaries from adjacent nodes',
    4: 'Showing high-level overview with node summaries only',
    5: 'Showing entire conversation arc summary',
  };

  return descriptions[zoomLevel] || descriptions[3];
}

/**
 * Check if node can be edited
 * @param {Object} node - Node object
 * @param {Object} user - Current user object
 * @returns {boolean} Whether node can be edited
 */
export function canEditNode(node, user) {
  // For now, all nodes are editable
  // Can add permissions logic later
  return true;
}

/**
 * Validate node edits
 * @param {Object} originalNode - Original node
 * @param {Object} editedNode - Edited node
 * @returns {Object} Validation result { valid, errors }
 */
export function validateNodeEdits(originalNode, editedNode) {
  const errors = [];

  // Title validation
  if (!editedNode.title || editedNode.title.trim().length === 0) {
    errors.push('Title cannot be empty');
  }
  if (editedNode.title && editedNode.title.length > 200) {
    errors.push('Title must be 200 characters or less');
  }

  // Summary validation
  if (editedNode.summary && editedNode.summary.length > 2000) {
    errors.push('Summary must be 2000 characters or less');
  }

  // Keywords validation
  if (editedNode.keywords && editedNode.keywords.length > 20) {
    errors.push('Maximum 20 keywords allowed');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Get differences between original and edited node
 * @param {Object} originalNode - Original node
 * @param {Object} editedNode - Edited node
 * @returns {Object} Object containing changed fields
 */
export function getNodeDiff(originalNode, editedNode) {
  const diff = {};

  if (originalNode.title !== editedNode.title) {
    diff.title = { old: originalNode.title, new: editedNode.title };
  }
  if (originalNode.summary !== editedNode.summary) {
    diff.summary = { old: originalNode.summary, new: editedNode.summary };
  }

  // Check keywords array
  const oldKeywords = JSON.stringify(originalNode.keywords || []);
  const newKeywords = JSON.stringify(editedNode.keywords || []);
  if (oldKeywords !== newKeywords) {
    diff.keywords = { old: originalNode.keywords, new: editedNode.keywords };
  }

  return diff;
}

export default {
  getContextConfig,
  getContextNodes,
  formatUtterances,
  getContextDescription,
  canEditNode,
  validateNodeEdits,
  getNodeDiff,
};
