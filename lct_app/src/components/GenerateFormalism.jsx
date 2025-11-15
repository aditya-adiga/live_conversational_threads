import { useState, useRef, useEffect } from "react";
import { authenticatedFetch } from "../utils/api";

export default function GenerateFormalism({
  chunkDict,
  graphData,
  isFormalismView,
  setIsFormalismView,
  formalismData,
  setFormalismData,
}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [userPrefDraft, setUserPrefDraft] = useState("");
  const [userPref, setUserPref] = useState("");
  const [lastUsedPref, setLastUsedPref] = useState("");
  const dialogRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);

  const latestChunk = graphData?.[graphData.length - 1] || [];

  const handleFormalismGenerate = async () => {
    const dataForFormalism = {
      chunks: chunkDict || {},
      graph_data: graphData || {},
      user_pref: userPref,
    };

    setIsLoading(true);

    try {
      const response = await authenticatedFetch("/generate_formalism/", {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
        body: JSON.stringify(dataForFormalism),
      });

      if (!response.ok) throw new Error("Failed to generate formalisms");

      const data = await response.json();
      setFormalismData(data);
      setLastUsedPref(userPref); // Update last used pref here
      setIsFormalismView(true); // Switch view after successful generation
    } catch (error) {
      console.error("Error generating Formalisms:", error);
      alert("Error generating Formalisms. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Simplified button click handler
  const handleMainButtonClick = () => {
    if (isFormalismView) {
      setIsFormalismView(false);
    } else {
      // Always regenerate if:
      // 1. No formalism data exists
      // 2. User preference has changed
      // 3. Or if we're not currently loading
      if (!formalismData || userPref !== lastUsedPref || !isLoading) {
        handleFormalismGenerate();
      } else {
        setIsFormalismView(true);
      }
    }
  };

  // Close dialog when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dialogRef.current && !dialogRef.current.contains(event.target)) {
        setIsDialogOpen(false);
      }
    };

    if (isDialogOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDialogOpen]);

  return (
    <div className="relative flex flex-col md:flex-row items-end md:items-center gap-2 w-full md:w-auto">
      {/* User research interest button */}
      {!isFormalismView && (
        <button
          className="w-full md:w-auto px-3 py-1.5 text-sm md:px-4 md:py-2 md:text-base bg-white text-blue-700 font-semibold rounded-lg shadow hover:bg-gray-100 text-center"
          onClick={() => {
            setIsDialogOpen(true);
            setUserPrefDraft(userPref);
          }}
        >
          User Research Interest
        </button>
      )}
  
      {/* Main action button */}
      <button
        className={`w-full md:w-auto px-3 py-1.5 text-sm md:px-4 md:py-2 md:text-base font-semibold rounded-lg shadow transition text-center ${
          (!userPref || latestChunk.length === 0 || isLoading) &&
          !isFormalismView
            ? "bg-gray-200 text-gray-500 cursor-not-allowed"
            : "bg-white text-purple-700 hover:bg-gray-100"
        }`}
        onClick={handleMainButtonClick}
        disabled={
          (!userPref || latestChunk.length === 0 || isLoading) &&
          !isFormalismView
        }
      >
        {isLoading
          ? "Generating..."
          : isFormalismView
          ? "Browse Conversation"
          : "Generate Formalism"}
      </button>
  
      {/* Dialog Box */}
      {isDialogOpen && (
        <div
          ref={dialogRef}
          className="absolute top-[110%] left-1/2 transform -translate-x-1/2 sm:left-auto sm:right-0 sm:transform-none sm:translate-x-0 bg-white text-black p-4 rounded-lg shadow-xl border w-[90vw] sm:w-[24rem] max-w-[350px] max-h-[70vh] overflow-auto z-80"
        >
          <h2 className="text-lg font-bold mb-3">
            Enter your research interests
          </h2>
  
          <textarea
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Enter research interest or field along which you want to explore formalisms..."
            value={userPrefDraft}
            rows="2"
            onChange={(e) => setUserPrefDraft(e.target.value)}
          />
  
          <div className="flex justify-end space-x-2 mt-4">
            <button
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </button>
            <button
              className={`px-4 py-2 rounded-lg shadow-md text-sm font-semibold ${
                !userPrefDraft.trim()
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-green-300 hover:bg-green-400 text-white"
              }`}
              onClick={() => {
                setUserPref(userPrefDraft.trim());
                setIsDialogOpen(false);
              }}
              disabled={!userPrefDraft.trim()}
            >
              Save preference
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
