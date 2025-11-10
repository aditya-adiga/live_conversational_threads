import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function ImportCanvas() {
  const [isImporting, setIsImporting] = useState(false);
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const API_URL = import.meta.env.VITE_API_URL || "";

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file extension
    if (!file.name.endsWith(".canvas")) {
      alert("Please select a valid .canvas file");
      return;
    }

    // Read file content
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const canvasData = JSON.parse(e.target.result);
        await handleImport(canvasData, file.name);
      } catch (error) {
        console.error("Failed to parse canvas file:", error);
        alert("Invalid canvas file format");
      }
    };
    reader.readAsText(file);
  };

  const handleImport = async (canvasData, originalFileName) => {
    setIsImporting(true);

    try {
      // Extract name without .canvas extension
      const baseName = originalFileName.replace(".canvas", "");

      const response = await fetch(`${API_URL}/import/obsidian-canvas/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          canvas_data: canvasData,
          file_name: fileName || baseName,
          preserve_positions: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Import failed");
      }

      const result = await response.json();
      console.log("Canvas imported successfully:", result);
      alert(`Successfully imported: ${result.file_name}`);

      // Navigate to the newly imported conversation
      navigate(`/view/${result.file_id}`);
    } catch (error) {
      console.error("Failed to import canvas:", error);
      alert(`Failed to import canvas: ${error.message}`);
    } finally {
      setIsImporting(false);
      setFileName("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col gap-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".canvas"
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />

      <button
        className={`px-4 py-2 rounded-lg shadow-md text-sm font-semibold whitespace-nowrap transition
          ${
            isImporting
              ? "bg-gray-200 cursor-not-allowed"
              : "bg-indigo-500 hover:bg-indigo-600 text-white"
          }`}
        onClick={handleButtonClick}
        disabled={isImporting}
        title="Import Obsidian Canvas file"
      >
        {isImporting ? "Importing..." : "Import from Canvas"}
      </button>

      {/* Optional: Name input for the imported conversation */}
      <input
        type="text"
        placeholder="Optional: Custom name"
        value={fileName}
        onChange={(e) => setFileName(e.target.value)}
        className="px-2 py-1 text-xs rounded border border-gray-300 text-gray-800"
        disabled={isImporting}
      />
    </div>
  );
}
