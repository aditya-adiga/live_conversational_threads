import { useState, useEffect } from "react";
import { saveConversationToServer } from "../utils/SaveConversation";

export default function SaveJson({ chunkDict, graphData, conversationId, setMessage, message, fileName, setFileName, firebaseUid }) {
  

  const isSaveDisabled =
    !chunkDict || Object.keys(chunkDict).length === 0 || !graphData || graphData.length === 0 || !firebaseUid;

  const handleSave = async () => {
    if (isSaveDisabled) return;

    const newName = prompt("Enter a name for your conversation file:", fileName || "");
    if (!newName) {
      setMessage("Save canceled. No file name provided.");
      return;
    }

    setFileName(newName);

    try {
      const result = await saveConversationToServer({
        fileName: newName,
        chunkDict,
        graphData,
        conversationId,
        firebaseUid,
      });

      setMessage(`Conversation "${newName}" saved. ${result.message}`);
    } catch (err) {
      console.error("Save failed:", err);
      setMessage("Error saving conversation.");
    }
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
        title={isSaveDisabled ? (!firebaseUid ? "Sign in to save" : "No data to save") : "Export conversation"}
      >
        Rename Conversation
      </button>

      {message && (
        <div className="text-sm text-white bg-gray-900 px-3 py-1 rounded shadow">
          {message}
        </div>
      )}
    </div>
  );
}