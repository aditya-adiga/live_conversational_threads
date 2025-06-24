const API_URL = import.meta.env.VITE_API_URL || "";

export async function saveConversationToServer({ fileName, chunkDict, graphData, conversationId }) {
  if (!fileName || !chunkDict || !graphData) return { success: false, message: "Missing data" };

  try {
    const response = await fetch(`${API_URL}/save_json/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
    } catch (e) {
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