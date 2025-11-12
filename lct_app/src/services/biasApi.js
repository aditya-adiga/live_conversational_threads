/**
 * Cognitive Bias Analysis API Client
 * Week 12: Advanced AI Analysis
 *
 * Client for interacting with cognitive bias detection endpoints
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

/**
 * Analyze all nodes in a conversation for cognitive biases
 *
 * @param {string} conversationId - Conversation UUID
 * @param {boolean} forceReanalysis - Re-analyze even if already done
 * @returns {Promise<{
 *   total_nodes: number,
 *   analyzed: number,
 *   nodes_with_biases: number,
 *   bias_count: number,
 *   by_category: object,
 *   by_bias: object,
 *   nodes: Array
 * }>}
 */
export async function analyzeCognitiveBiases(conversationId, forceReanalysis = false) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/biases/analyze?force_reanalysis=${forceReanalysis}`;

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
 * Get existing cognitive bias analysis results for a conversation
 */
export async function getBiasResults(conversationId) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/biases`;

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
 * Get cognitive bias analyses for a specific node
 */
export async function getNodeBiases(nodeId) {
  const url = `${API_BASE_URL}/api/nodes/${nodeId}/biases`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to get node biases: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get category information and styling
 */
export function getCategoryInfo(category) {
  const categories = {
    confirmation: {
      name: "Confirmation Biases",
      description: "Seeking information that confirms existing beliefs",
      color: "text-purple-700",
      bgColor: "bg-purple-100",
      borderColor: "border-purple-300"
    },
    memory: {
      name: "Memory Biases",
      description: "Distortions in how we recall information",
      color: "text-blue-700",
      bgColor: "bg-blue-100",
      borderColor: "border-blue-300"
    },
    social: {
      name: "Social Biases",
      description: "Influence of group dynamics and social pressure",
      color: "text-green-700",
      bgColor: "bg-green-100",
      borderColor: "border-green-300"
    },
    decision: {
      name: "Decision-Making Biases",
      description: "Systematic errors in judgment",
      color: "text-orange-700",
      bgColor: "bg-orange-100",
      borderColor: "border-orange-300"
    },
    attribution: {
      name: "Attribution Biases",
      description: "How we explain behavior and events",
      color: "text-yellow-700",
      bgColor: "bg-yellow-100",
      borderColor: "border-yellow-300"
    },
    logical: {
      name: "Logical Fallacies",
      description: "Errors in reasoning and argumentation",
      color: "text-red-700",
      bgColor: "bg-red-100",
      borderColor: "border-red-300"
    }
  };

  return categories[category] || {
    name: category,
    description: "Unknown category",
    color: "text-gray-700",
    bgColor: "bg-gray-100",
    borderColor: "border-gray-300"
  };
}

/**
 * Get bias-specific information
 */
export function getBiasInfo(biasType) {
  const biases = {
    // Confirmation Biases
    confirmation_bias: "Confirmation Bias: Favoring information that confirms pre-existing beliefs",
    cherry_picking: "Cherry Picking: Selecting only supporting data while ignoring contradictory evidence",
    motivated_reasoning: "Motivated Reasoning: Reasoning to reach a desired conclusion",
    belief_perseverance: "Belief Perseverance: Maintaining beliefs despite contradictory evidence",

    // Memory Biases
    hindsight_bias: "Hindsight Bias: Believing past events were more predictable than they were",
    availability_heuristic: "Availability Heuristic: Overestimating likelihood based on memorability",
    recency_bias: "Recency Bias: Giving undue weight to recent events",
    false_memory: "False Memory: Remembering events incorrectly",

    // Social Biases
    groupthink: "Groupthink: Desire for harmony leading to poor decisions",
    authority_bias: "Authority Bias: Overvaluing opinions of authority figures",
    bandwagon_effect: "Bandwagon Effect: Following the crowd",
    halo_effect: "Halo Effect: Positive impression influencing overall judgment",
    in_group_bias: "In-Group Bias: Favoring one's own group over outsiders",

    // Decision-Making Biases
    anchoring: "Anchoring Bias: Over-relying on first piece of information",
    sunk_cost_fallacy: "Sunk Cost Fallacy: Continuing based on past investment",
    status_quo_bias: "Status Quo Bias: Preferring current state over change",
    optimism_bias: "Optimism Bias: Overestimating likelihood of positive outcomes",
    planning_fallacy: "Planning Fallacy: Underestimating time, costs, and risks",

    // Attribution Biases
    fundamental_attribution_error: "Fundamental Attribution Error: Overemphasizing personality vs situation",
    self_serving_bias: "Self-Serving Bias: Success = me, failure = external",
    just_world_hypothesis: "Just World Hypothesis: Believing people get what they deserve",

    // Logical Fallacies
    slippery_slope: "Slippery Slope: Assuming chain of negative consequences",
    straw_man: "Straw Man: Misrepresenting arguments to attack them",
    false_dichotomy: "False Dichotomy: Presenting only two options when more exist",
    ad_hominem: "Ad Hominem: Attacking the person rather than the argument",
    appeal_to_emotion: "Appeal to Emotion: Manipulating emotions vs. reasoning",
    hasty_generalization: "Hasty Generalization: Broad conclusions from limited evidence"
  };

  return biases[biasType] || biasType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get severity level description
 */
export function getSeverityLevel(severity) {
  if (severity >= 0.8) return { level: "High", color: "text-red-600" };
  if (severity >= 0.5) return { level: "Medium", color: "text-orange-600" };
  return { level: "Low", color: "text-yellow-600" };
}
