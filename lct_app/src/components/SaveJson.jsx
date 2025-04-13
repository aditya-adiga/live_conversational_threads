import { useState, useRef, useEffect } from "react";

export default function SaveJson({ chunkDict, graphData }) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [fileName, setFileName] = useState("");
  const dialogRef = useRef(null);

  // Disable Save if no chunkDict or graphData is available
  const isSaveDisabled = !graphData || Object.keys(graphData).length === 0;

  // Close dialog if clicked outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dialogRef.current && !dialogRef.current.contains(event.target)) {
        setIsDialogOpen(false);
      }
    }

    if (isDialogOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDialogOpen]);

  const handleSave = async () => {
    if (!fileName.trim()) {
      alert("Please enter a valid filename!");
      return;
    }

    const dataToSave = {
      file_name: fileName.trim(),
      chunks: chunkDict || {}, // Ensure it's an object
      graph_data: graphData || {}, // Ensure it's an object
    };

    try {
      const response = await fetch("http://localhost:8000/save_json/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(dataToSave),
      });

      if (!response.ok) {
        throw new Error("Failed to save JSON");
      }

      alert("Live Conversation Thread saved successfully!");
      setIsDialogOpen(false);
      setFileName(""); // Reset input field
    } catch (error) {
      console.error("Error saving JSON:", error);
      alert("Error saving JSON. Please try again.");
    }
  };

  return (
    <div className="relative">
      {/* Save Button */}
      <button
        className={`absolute top-4 right-4 px-3 py-1.5 rounded-lg shadow-md text-sm font-semibold whitespace-nowrap  
                  ${
                    isSaveDisabled
                      ? "bg-gray-200 cursor-not-allowed"
                      : "bg-green-200 hover:bg-green-300 text-white"
                  }`}
        onClick={() => !isSaveDisabled && setIsDialogOpen(true)}
        disabled={isSaveDisabled}
      >
        Save Conversation
      </button>

      {/* Dialog Box */}
      {isDialogOpen && (
        <div
          ref={dialogRef}
          className="absolute top-12 right-4 bg-white p-4 rounded-lg shadow-xl border w-80 text-black"
        >
          <h2 className="text-lg font-bold mb-3">Enter File Name</h2>

          <input
            type="text"
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Enter file name..."
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
          />

          <div className="flex justify-end space-x-2 mt-4">
            <button
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </button>
            <button
              className={`px-4 py-2 rounded-lg shadow-md text-sm font-semibold 
                          ${
                            !fileName.trim()
                              ? "bg-gray-200 cursor-not-allowed"
                              : "bg-green-200 hover:bg-green-300 text-white"
                          }`}
              onClick={handleSave}
              disabled={!fileName.trim()} // Disable if filename is empty
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
