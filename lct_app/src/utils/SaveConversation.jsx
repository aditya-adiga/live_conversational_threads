import { saveUserConversation } from './api.js';

export async function saveConversationToServer({ fileName, chunkDict, graphData, conversationId }) {
  return await saveUserConversation({ fileName, chunkDict, graphData, conversationId });
}