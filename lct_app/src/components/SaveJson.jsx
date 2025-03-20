import { useState, useRef, useEffect } from "react";

export default function SaveJson({ chunkDict, finalJson, isSaveDisabled }) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [fileName, setFileName] = useState("");
  const dialogRef = useRef(null);

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
      file_name: fileName,
      chunks: chunkDict,
      final_output: finalJson,
    };

    try {
      const response = await fetch("http://localhost:8000/save_json/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dataToSave),
      });

      if (!response.ok) {
        throw new Error("Failed to save JSON");
      }

      alert("JSON saved successfully!");
      setIsDialogOpen(false);
      setFileName(""); // Reset input field
    } catch (error) {
      console.error("Error saving JSON:", error);
      alert("Error saving JSON. Please try again.");
    }
  };

  return (
    <div className="relative">
      {/* Save Button (Only Disabled When There’s No Data) */}
      <button
        className={`absolute top-4 right-4 px-3 py-1.5 rounded-lg shadow-md text-sm font-semibold 
                    ${isSaveDisabled ? "bg-gray-400 cursor-not-allowed" : "bg-yellow-400 hover:bg-yellow-500 text-white"}`}
        onClick={() => !isSaveDisabled && setIsDialogOpen(true)}
        disabled={isSaveDisabled}
      >
        Save JSON
      </button>

      {/* Dialog Box (Appears on top, no background overlay) */}
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
              className="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded-lg"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </button>
            <button
              className={`px-4 py-2 rounded-lg shadow-md text-sm font-semibold 
                          ${!fileName.trim() ? "bg-gray-400 cursor-not-allowed" : "bg-green-500 hover:bg-green-600 text-white"}`}
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