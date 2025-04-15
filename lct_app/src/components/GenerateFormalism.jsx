import { useState, useRef, useEffect } from "react";

export default function GenerateFormalism({
  graphData,
  isFormalismView,
  setIsFormalismView,
}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false); // for preference dialogue box
  const [userPrefDraft, setUserPrefDraft] = useState(""); // for saving temporary state of preference
  const [userPref, setUserPref] = useState(""); // Stores user preference or wish
  const dialogRef = useRef(null); // for identifying click outside

  const latestChunk = graphData?.[graphData.length - 1] || []; // latest graph data recieved.

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
    <div className="relative w-full flex justify-center mb-4">
      <div className="flex space-x-2">
        {/* User research interest button */}
        {!isFormalismView && (
          <button
            className="px-4 py-2 bg-white text-blue-700 font-semibold rounded-lg shadow hover:bg-gray-100"
            onClick={() => {
              setIsDialogOpen(true);
              setUserPrefDraft(userPref);
              console.log(userPref);
            }}
          >
            User Research Interest
          </button>
        )}

        {/* Get Formalism List */}
        <button
          className={`px-4 py-2 font-semibold rounded-lg shadow 
            ${
              (!userPref || latestChunk.length === 0) && !isFormalismView
                ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                : "bg-white text-purple-700 hover:bg-gray-100"
            }`}
          onClick={() => {
            setIsFormalismView((prev) => !prev);
          }}
          disabled={(!userPref || latestChunk.length === 0) && !isFormalismView}
        >
          {isFormalismView ? "Browse Conversation" : "Generate Formalism"}
        </button>
      </div>

      {/* Dialog Box */}
      {isDialogOpen && (
        <div
          ref={dialogRef}
          className="absolute bottom-14 bg-white text-black p-4 rounded-lg shadow-xl border w-200 z-20"
        >
          <h2 className="text-lg font-bold mb-3">
            Enter your research interests
          </h2>

          <textarea
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Enter research interest or field along which you want to explore formalisms..."
            value={userPrefDraft}
            rows="2" // Adjust this based on how tall you want the text area
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
              className={`px-4 py-2 rounded-lg shadow-md text-sm font-semibold 
                            ${
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
