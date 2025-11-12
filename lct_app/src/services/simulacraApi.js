/**
 * Simulacra Analysis API Client
 * Week 11: Advanced AI Analysis
 *
 * Client for interacting with Simulacra level detection endpoints
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

/**
 * Analyze all nodes in a conversation for Simulacra levels
 *
 * @param {string} conversationId - Conversation UUID
 * @param {boolean} forceReanalysis - Re-analyze even if already done
 * @returns {Promise<{
 *   total_nodes: number,
 *   analyzed: number,
 *   distribution: {1: number, 2: number, 3: number, 4: number},
 *   nodes: Array<{node_id, node_name, level, confidence, reasoning, examples}>
 * }>}
 */
export async function analyzeSimulacraLevels(conversationId, forceReanalysis = false) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/simulacra/analyze?force_reanalysis=${forceReanalysis}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Analysis failed: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get existing Simulacra analysis results for a conversation
 *
 * @param {string} conversationId - Conversation UUID
 * @returns {Promise<{
 *   total_nodes: number,
 *   analyzed: number,
 *   distribution: {1: number, 2: number, 3: number, 4: number},
 *   nodes: Array<{node_id, node_name, level, confidence, reasoning, examples, analyzed_at}>
 * }>}
 */
export async function getSimulacraResults(conversationId) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/simulacra`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to get results: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get Simulacra analysis for a specific node
 *
 * @param {string} nodeId - Node UUID
 * @returns {Promise<{
 *   level: number,
 *   confidence: number,
 *   reasoning: string,
 *   examples: string[],
 *   analyzed_at: string
 * }>}
 */
export async function getNodeSimulacra(nodeId) {
  const url = `${API_BASE_URL}/api/nodes/${nodeId}/simulacra`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    if (response.status === 404) {
      return null; // No analysis exists yet
    }
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to get node Simulacra: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get level description and color
 *
 * @param {number} level - Simulacra level (1-4)
 * @returns {{name: string, description: string, color: string, bgColor: string}}
 */
export function getLevelInfo(level) {
  const levels = {
    1: {
      name: "Reflection of Reality",
      description: "Direct factual statements and observable events",
      color: "text-blue-700",
      bgColor: "bg-blue-100",
      borderColor: "border-blue-300",
      examples: ["The meeting started at 2 PM", "There are 5 people present"]
    },
    2: {
      name: "Perversion of Reality",
      description: "Interpretations, opinions, and subjective representations",
      color: "text-green-700",
      bgColor: "bg-green-100",
      borderColor: "border-green-300",
      examples: ["I think this is productive", "The document seems comprehensive"]
    },
    3: {
      name: "Pretense of Reality",
      description: "Hypotheticals and speculation masking uncertainty",
      color: "text-orange-700",
      bgColor: "bg-orange-100",
      borderColor: "border-orange-300",
      examples: ["This will solve all problems", "Obviously the best approach"]
    },
    4: {
      name: "Pure Simulacrum",
      description: "Abstract concepts disconnected from verifiable reality",
      color: "text-red-700",
      bgColor: "bg-red-100",
      borderColor: "border-red-300",
      examples: ["Paradigm shift", "Leverage synergies", "Market forces optimize"]
    }
  };

  return levels[level] || levels[2]; // Default to level 2 if invalid
}
