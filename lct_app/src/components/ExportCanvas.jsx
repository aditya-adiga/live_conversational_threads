import { useState } from "react";
import { useParams } from "react-router-dom";

export default function ExportCanvas({ graphData, fileName }) {
  const { conversationId } = useParams();
  const [isExporting, setIsExporting] = useState(false);
  const [includeChunks, setIncludeChunks] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "";

  const isExportDisabled = !graphData || graphData.length === 0 || !conversationId;

  const handleExport = async () => {
    if (isExportDisabled) {
      console.warn("Export action attempted while disabled.");
      return;
    }

    setIsExporting(true);

    try {
      const response = await fetch(
        `${API_URL}/export/obsidian-canvas/${conversationId}?include_chunks=${includeChunks}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      const canvasData = await response.json();

      // Download as .canvas file
      const blob = new Blob([JSON.stringify(canvasData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileName || "conversation"}.canvas`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log("Canvas exported successfully");
    } catch (error) {
      console.error("Failed to export canvas:", error);
      alert(`Failed to export canvas: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        className={`h-full px-4 py-2 rounded-lg shadow-md text-sm font-semibold whitespace-nowrap flex items-center transition
          ${
            isExportDisabled || isExporting
              ? "bg-gray-200 cursor-not-allowed"
              : "bg-purple-500 hover:bg-purple-600 text-white"
          }`}
        onClick={handleExport}
        disabled={isExportDisabled || isExporting}
        title={
          isExportDisabled
            ? "No data to export"
            : "Export as Obsidian Canvas"
        }
      >
        {isExporting ? "Exporting..." : "Export to Canvas"}
      </button>

      {/* Optional: Checkbox to include chunks */}
      {!isExportDisabled && (
        <label className="flex items-center text-xs text-white gap-1 cursor-pointer">
          <input
            type="checkbox"
            checked={includeChunks}
            onChange={(e) => setIncludeChunks(e.target.checked)}
            className="cursor-pointer"
          />
          Include chunks
        </label>
      )}
    </div>
  );
}
