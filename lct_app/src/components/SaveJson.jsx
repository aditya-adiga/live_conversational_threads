import { useState, useEffect } from "react";
import { saveConversationToServer } from "../utils/SaveConversation";

export default function SaveJson({ chunkDict, graphData, conversationId, setMessage, message }) {
  

  const isSaveDisabled =
    !chunkDict || Object.keys(chunkDict).length === 0 || !graphData || graphData.length === 0;

  const handleSave = async () => {
    if (isSaveDisabled) return;

    const fileName = prompt("Enter a name for your conversation file:");
    if (!fileName) {
      setMessage("Save canceled. No file name provided.");
      return;
    }

    const result = await saveConversationToServer({
      fileName,
      chunkDict,
      graphData,
      conversationId,
    });

    setMessage(result.message);
  };

  useEffect(() => {
    if (!message) return;

    const handleClick = () => {
      setMessage("");
    };

    window.addEventListener("click", handleClick);

    return () => {
      window.removeEventListener("click", handleClick);
    };
  }, [message]);

  return (
    <div className="flex flex-col items-center space-y-2">
      <button
        className={`px-4 py-2 rounded-lg text-sm font-semibold  
          ${
            isSaveDisabled
              ? "bg-gray-200 cursor-not-allowed"
              : "bg-blue-300 hover:bg-blue-400 text-white"
          }`}
        onClick={handleSave}
        disabled={isSaveDisabled}
        title={isSaveDisabled ? "No data to save" : "Export conversation"}
      >
        Add Conversation to Archive
      </button>

      {message && (
        <div className="text-sm text-white bg-gray-900 px-3 py-1 rounded shadow">
          {message}
        </div>
      )}
    </div>
  );
}