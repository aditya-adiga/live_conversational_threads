import { auth } from '../config/firebase';

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Get the current user's Firebase ID token
 */
export async function getAuthToken() {
  try {
    if (!auth.currentUser) {
      throw new Error('User not authenticated');
    }
    return await auth.currentUser.getIdToken();
  } catch (error) {
    console.error('Error getting auth token:', error);
    throw error;
  }
}

/**
 * Make authenticated API requests
 */
export async function authenticatedFetch(url, options = {}) {
  try {
    const token = await getAuthToken();
    
    const authHeaders = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(`${API_URL}${url}`, {
      ...options,
      headers: authHeaders
    });

    if (response.status === 401) {
      throw new Error('Authentication failed. Please sign in again.');
    }

    return response;
  } catch (error) {
    console.error('Authenticated fetch error:', error);
    throw error;
  }
}

/**
 * Get conversations for the current user based on view type
 * @param {string} viewType - 'all', 'owned', or 'shared'
 */
export async function getUserConversations(viewType = 'all') {
  try {
    let endpoint;
    switch (viewType) {
      case 'owned':
        endpoint = '/conversations/owned/';
        break;
      case 'shared':
        endpoint = '/conversations/shared/';
        break;
      case 'all':
      default:
        endpoint = '/conversations/';
        break;
    }

    const response = await authenticatedFetch(endpoint);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch conversations');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user conversations:', error);
    throw error;
  }
}

/**
 * Get a specific conversation by ID
 */
export async function getUserConversation(conversationId) {
  try {
    const response = await authenticatedFetch(`/conversations/${conversationId}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch conversation');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching conversation:', error);
    throw error;
  }
}

/**
 * Save conversation data
 */
export async function saveUserConversation({ fileName, chunkDict, graphData, conversationId }) {
  if (!fileName || !chunkDict || !graphData) {
    return { success: false, message: "Missing data" };
  }

  try {
    const response = await authenticatedFetch('/save_json/', {
      method: 'POST',
      body: JSON.stringify({
        file_name: fileName.trim(),
        chunks: chunkDict,
        graph_data: graphData,
        conversation_id: conversationId,
      }),
    });

    const text = await response.text();
    let result = {};

    try {
      result = text ? JSON.parse(text) : {};
    } catch {
      console.warn("Invalid JSON response:", text);
    }

    return {
      success: response.ok,
      message: result.message || result.detail || (response.ok ? "Saved!" : "Save failed"),
    };
  } catch (err) {
    console.error("Save failed:", err);
    return { success: false, message: err.message || "Error saving" };
  }
}

/**
 * Share a conversation with other users
 */
export async function shareConversation(conversationId, emails) {
  try {
    const response = await authenticatedFetch(`/conversations/${conversationId}/share`, {
      method: 'POST',
      body: JSON.stringify({
        conversation_id: conversationId,
        emails: emails
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to share conversation');
    }

    return await response.json();
  } catch (error) {
    console.error('Error sharing conversation:', error);
    throw error;
  }
}

/**
 * Get users that a conversation is shared with
 */
export async function getSharedUsers(conversationId) {
  try {
    const response = await authenticatedFetch(`/conversations/${conversationId}/shared-users`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to get shared users');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting shared users:', error);
    throw error;
  }
}

/**
 * Remove a user from conversation sharing
 */
export async function removeSharedUser(conversationId, userUid) {
  try {
    const response = await authenticatedFetch(`/conversations/${conversationId}/shared-users`, {
      method: 'DELETE',
      body: JSON.stringify({
        user_uid: userUid
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to remove user');
    }

    return await response.json();
  } catch (error) {
    console.error('Error removing shared user:', error);
    throw error;
  }
}