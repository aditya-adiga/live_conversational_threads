/**
 * API Client for Edit History & Training Data Export
 *
 * Connects to the FastAPI backend edit history endpoints (Week 10).
 * Handles fetching edits, statistics, and exporting training data.
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

/**
 * Get all edits for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @param {Object} options - Query options
 * @returns {Promise<Object>} List of edits
 */
export async function getConversationEdits(conversationId, options = {}) {
  const {
    limit = null,
    offset = 0,
    targetType = null,
    unexportedOnly = false
  } = options;

  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);
  if (targetType) params.append('target_type', targetType);
  if (unexportedOnly) params.append('unexported_only', 'true');

  const url = `${API_BASE_URL}/api/conversations/${conversationId}/edits?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch edits: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get edit statistics for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @returns {Promise<Object>} Edit statistics
 */
export async function getEditStatistics(conversationId) {
  const url = `${API_BASE_URL}/api/conversations/${conversationId}/edits/statistics`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch statistics: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Export training data for a conversation
 * @param {string} conversationId - UUID of the conversation
 * @param {string} format - Export format ('jsonl', 'csv', 'markdown')
 * @param {boolean} unexportedOnly - Only export unexported edits
 * @returns {Promise<Blob>} Exported data as Blob
 */
export async function exportTrainingData(conversationId, format = 'jsonl', unexportedOnly = false) {
  const params = new URLSearchParams();
  params.append('format', format);
  if (unexportedOnly) params.append('unexported_only', 'true');

  const url = `${API_BASE_URL}/api/conversations/${conversationId}/training-data?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to export training data: ${response.statusText}`);
  }

  return await response.blob();
}

/**
 * Download exported training data as file
 * @param {string} conversationId - UUID of the conversation
 * @param {string} format - Export format
 * @param {boolean} unexportedOnly - Only export unexported edits
 */
export async function downloadTrainingData(conversationId, format = 'jsonl', unexportedOnly = false) {
  try {
    const blob = await exportTrainingData(conversationId, format, unexportedOnly);

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Generate filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const convShort = conversationId.substring(0, 8);
    a.download = `training_${convShort}_${timestamp}.${format}`;

    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return true;
  } catch (error) {
    console.error('Failed to download training data:', error);
    throw error;
  }
}

/**
 * Add feedback to an edit
 * @param {string} editId - UUID of the edit
 * @param {string} feedbackText - Feedback text
 * @returns {Promise<Object>} Success status
 */
export async function addEditFeedback(editId, feedbackText) {
  const url = `${API_BASE_URL}/api/edits/${editId}/feedback`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: feedbackText
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to add feedback: ${response.statusText}`);
  }

  return await response.json();
}
