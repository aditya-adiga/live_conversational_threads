import { useState, useRef, useEffect } from "react";

export default function SaveJson({ chunkDict}) {
  const isSaveDisabled = !chunkDict || Object.keys(chunkDict).length === 0;

  const handleSave = () => {
    if (isSaveDisabled) {
      console.warn("Save action attempted while disabled.");
      return;
    }

    // Combine all chunk values into a readable text format
    const combinedText = Object.entries(chunkDict)
      .map(([id, content]) => `--- Chunk ID: ${id} ---\n${content}`)
      .join("\n\n");

    const blob = new Blob([combinedText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "conversation_transcript.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative">
      <button
        className={`absolute top-4 right-4 px-3 py-1.5 rounded-lg shadow-md text-sm font-semibold whitespace-nowrap  
                  ${
                    isSaveDisabled
                      ? "bg-gray-200 cursor-not-allowed"
                      : "bg-green-300 hover:bg-green-400 text-white"
                  }`}
        onClick={handleSave}
        disabled={isSaveDisabled}
        title={isSaveDisabled ? "No data to save" : "Export transcript"}
      >
        Download Transcript
      </button>
    </div>
  );
}