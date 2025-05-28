import { useState, useRef, useEffect } from "react"; 

export default function SaveJson({ chunkDict, graphData, setGraphData }) {
  // Disable Save if no graphData is available or if it's an empty object
  const isSaveDisabled = !graphData || Object.keys(graphData).length === 0;

  const handleSave = () => {
    // Prevent action if the button is disabled (though it shouldn't be clickable)
    if (isSaveDisabled) {
      console.warn("Save action attempted while disabled.");
      return;
    }

    const dataToSave = {
      chunks: chunkDict || {}, 
      graph_data: graphData || {},
    };

    const jsonString = JSON.stringify(dataToSave, null, 2);

    // A Blob is a file-like object of immutable, raw data.
    const blob = new Blob([jsonString], { type: "application/json" });

    // This URL can be used as a source for downloads.
    const url = URL.createObjectURL(blob);

    // Create a temporary anchor element to trigger the download
    const a = document.createElement("a");
    a.href = url;
    a.download = "conversation_data.json";

    // Append the anchor to the body, click it, and then remove it
    document.body.appendChild(a);
    a.click(); // Programmatically click the anchor to trigger download
    document.body.removeChild(a); // Clean up by removing the temporary anchor

    // Revoke the object URL to free up resources
    // This is important for performance and memory management.
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative">
      {/* Save Button */}
      <button
        className={`absolute top-4 right-4 px-3 py-1.5 rounded-lg shadow-md text-sm font-semibold whitespace-nowrap  
                  ${
                    isSaveDisabled
                      ? "bg-gray-200 cursor-not-allowed" // Reverted to original disabled style
                      : "bg-green-300 hover:bg-green-400 text-white" // Reverted to original enabled style
                  }`}
        onClick={handleSave} // Directly call handleSave when clicked
        disabled={isSaveDisabled}
        title={isSaveDisabled ? "No data to save" : "Export conversation"} // Add a title for better UX
      >
        Save Conversation
      </button>
      {/* The custom dialog box for filename input has been removed. */}
    </div>
  );
}
