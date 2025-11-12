/**
 * Implicit Frame Detection API Client
 * Week 13: Advanced AI Analysis
 *
 * Client for interacting with implicit frame detection endpoints
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

/**
 * Analyze all nodes in a conversation for implicit frames
 *
 * @param {string} conversationId - Conversation UUID
 * @param {boolean} forceReanalysis - Re-analyze even if already done
 * @returns {Promise<{
 *   total_nodes: number,
 *   analyzed: number,
 *   nodes_with_frames: number,
 *   frame_count: number,
 *   by_category: object,
 *   by_frame: object,
 *   nodes: Array
 * }>}
 */
export async function analyzeImplicitFrames(conversationId, forceReanalysis = false) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/frames/analyze?force_reanalysis=${forceReanalysis}`;

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
 * Get existing implicit frame analysis results for a conversation
 */
export async function getFrameResults(conversationId) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/frames`;

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
 * Get implicit frame analyses for a specific node
 */
export async function getNodeFrames(nodeId) {
  const url = `${API_BASE_URL}/api/nodes/${nodeId}/frames`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to get node frames: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get frame category information and styling
 */
export function getCategoryInfo(category) {
  const categories = {
    economic: {
      name: "Economic Frames",
      description: "Assumptions about markets, value, and resource allocation",
      color: "text-purple-700",
      bgColor: "bg-purple-100",
      borderColor: "border-purple-300"
    },
    moral: {
      name: "Moral/Ethical Frames",
      description: "Underlying ethical principles and values",
      color: "text-blue-700",
      bgColor: "bg-blue-100",
      borderColor: "border-blue-300"
    },
    political: {
      name: "Political Frames",
      description: "Assumptions about power and governance",
      color: "text-green-700",
      bgColor: "bg-green-100",
      borderColor: "border-green-300"
    },
    scientific: {
      name: "Scientific/Epistemological Frames",
      description: "How we know and understand the world",
      color: "text-orange-700",
      bgColor: "bg-orange-100",
      borderColor: "border-orange-300"
    },
    cultural: {
      name: "Cultural Frames",
      description: "Identity, community, and social relations",
      color: "text-yellow-700",
      bgColor: "bg-yellow-100",
      borderColor: "border-yellow-300"
    },
    temporal: {
      name: "Temporal Frames",
      description: "Time, change, and progress perspectives",
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
 * Get frame-specific information
 */
export function getFrameInfo(frameType) {
  const frames = {
    // Economic Frames
    market_fundamentalism: "Market Fundamentalism: Markets are the best way to organize society",
    socialist_framework: "Socialist Framework: Collective ownership and equitable distribution",
    growth_imperative: "Growth Imperative: Continuous economic growth is necessary",
    scarcity_mindset: "Scarcity Mindset: Resources are fundamentally limited",
    abundance_mindset: "Abundance Mindset: There is enough for everyone",
    zero_sum_thinking: "Zero-Sum Thinking: One person's gain is another's loss",

    // Moral/Ethical Frames
    utilitarian: "Utilitarian: Maximizing overall good and happiness",
    deontological: "Deontological: Focus on duties and moral rules",
    virtue_ethics: "Virtue Ethics: Character and virtues matter most",
    care_ethics: "Care Ethics: Relationships and empathy",
    rights_based: "Rights-Based: Individual rights and freedoms",
    consequentialist: "Consequentialist: Judging actions by their outcomes",

    // Political Frames
    progressive: "Progressive: Social progress and reducing inequality",
    conservative: "Conservative: Tradition, stability, and gradual change",
    libertarian: "Libertarian: Individual liberty and minimal government",
    authoritarian: "Authoritarian: Strong central authority",
    egalitarian: "Egalitarian: Equality and equal treatment",
    meritocratic: "Meritocratic: Success based on individual merit",

    // Scientific/Epistemological Frames
    reductionist: "Reductionist: Breaking systems into component parts",
    holistic: "Holistic: Understanding as integrated wholes",
    empiricist: "Empiricist: Knowledge from observation and evidence",
    rationalist: "Rationalist: Knowledge from reason and logic",
    constructivist: "Constructivist: Knowledge is socially constructed",
    deterministic: "Deterministic: Events are causally determined",

    // Cultural Frames
    individualist: "Individualist: Individual autonomy as priority",
    collectivist: "Collectivist: Group harmony as priority",
    hierarchical: "Hierarchical: Acceptance of ranked social structures",
    egalitarian_cultural: "Egalitarian: Minimizing status differences",
    universalist: "Universalist: Universal principles apply to all",
    particularist: "Particularist: Context and circumstances matter",

    // Temporal Frames
    short_term_focus: "Short-Term Focus: Immediate concerns take priority",
    long_term_thinking: "Long-Term Thinking: Future impacts matter most",
    cyclical_view: "Cyclical View: Time as recurring patterns",
    linear_progress: "Linear Progress: Continuous forward progress",
    status_quo_permanence: "Status Quo Permanence: Current conditions will persist",
    radical_change: "Radical Change: Transformative disruption expected"
  };

  return frames[frameType] || frameType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get strength level description
 */
export function getStrengthLevel(strength) {
  if (strength >= 0.8) return { level: "Very Strong", color: "text-red-600" };
  if (strength >= 0.6) return { level: "Strong", color: "text-orange-600" };
  if (strength >= 0.4) return { level: "Moderate", color: "text-yellow-600" };
  return { level: "Weak", color: "text-gray-600" };
}
