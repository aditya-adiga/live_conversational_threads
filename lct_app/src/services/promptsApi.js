/**
 * API Client for Prompts Configuration Service
 *
 * Connects to the FastAPI backend prompts endpoints (Week 9).
 * Handles managing, editing, and versioning prompts.
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

/**
 * List all available prompts
 * @returns {Promise<Object>} List of prompt names
 */
export async function listPrompts() {
  const url = `${API_BASE_URL}/api/prompts`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to list prompts: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get complete prompts configuration
 * @returns {Promise<Object>} Full prompts.json content
 */
export async function getPromptsConfig() {
  const url = `${API_BASE_URL}/api/prompts/config`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to get prompts config: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get a specific prompt configuration
 * @param {string} promptName - Name of the prompt
 * @returns {Promise<Object>} Prompt configuration
 */
export async function getPrompt(promptName) {
  const url = `${API_BASE_URL}/api/prompts/${promptName}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get prompt: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get prompt metadata (without template)
 * @param {string} promptName - Name of the prompt
 * @returns {Promise<Object>} Prompt metadata
 */
export async function getPromptMetadata(promptName) {
  const url = `${API_BASE_URL}/api/prompts/${promptName}/metadata`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to get metadata: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Update a prompt configuration
 * @param {string} promptName - Name of the prompt
 * @param {Object} promptConfig - New prompt configuration
 * @param {string} userId - User making the change
 * @param {string} comment - Comment about the change
 * @returns {Promise<Object>} Success status
 */
export async function updatePrompt(promptName, promptConfig, userId = 'anonymous', comment = '') {
  const url = `${API_BASE_URL}/api/prompts/${promptName}`;

  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt_config: promptConfig,
      user_id: userId,
      comment: comment
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || `Failed to update prompt: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Delete a prompt
 * @param {string} promptName - Name of the prompt to delete
 * @param {string} userId - User making the deletion
 * @param {string} comment - Comment about the deletion
 * @returns {Promise<Object>} Success status
 */
export async function deletePrompt(promptName, userId = 'anonymous', comment = '') {
  const url = `${API_BASE_URL}/api/prompts/${promptName}?user_id=${encodeURIComponent(userId)}&comment=${encodeURIComponent(comment)}`;

  const response = await fetch(url, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to delete prompt: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get version history for a prompt
 * @param {string} promptName - Name of the prompt
 * @param {number} limit - Maximum number of versions to return
 * @returns {Promise<Object>} Version history
 */
export async function getPromptHistory(promptName, limit = 10) {
  const url = `${API_BASE_URL}/api/prompts/${promptName}/history?limit=${limit}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to get history: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Restore a prompt to a previous version
 * @param {string} promptName - Name of the prompt
 * @param {string} versionTimestamp - Timestamp of the version to restore
 * @param {string} userId - User performing the restore
 * @returns {Promise<Object>} Success status
 */
export async function restorePromptVersion(promptName, versionTimestamp, userId = 'anonymous') {
  const url = `${API_BASE_URL}/api/prompts/${promptName}/restore`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version_timestamp: versionTimestamp,
      user_id: userId
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to restore version: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Validate a prompt configuration without saving
 * @param {string} promptName - Name of the prompt (for context)
 * @param {Object} promptConfig - Prompt configuration to validate
 * @returns {Promise<Object>} Validation result
 */
export async function validatePrompt(promptName, promptConfig) {
  const url = `${API_BASE_URL}/api/prompts/${promptName}/validate`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(promptConfig),
  });

  if (!response.ok) {
    throw new Error(`Failed to validate prompt: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Force reload prompts from file (hot-reload)
 * @returns {Promise<Object>} Success status
 */
export async function reloadPrompts() {
  const url = `${API_BASE_URL}/api/prompts/reload`;

  const response = await fetch(url, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to reload prompts: ${response.statusText}`);
  }

  return await response.json();
}
