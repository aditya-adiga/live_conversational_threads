import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
// import Input from "./components/Input";
// import AudioInput from "../components/AudioInput";
import StructuralGraph from "../components/StructuralGraph";
import ContextualGraph from "../components/ContextualGraph";
// import SaveJson from "../components/SaveJson";
import SaveTranscript from "../components/SaveTranscript";
import ExportCanvas from "../components/ExportCanvas";
import Legend from "../components/Legend";
import GenerateFormalism from "../components/GenerateFormalism";
import FormalismList from "../components/FormalismList";

export default function ViewConversation() {
  const [graphData, setGraphData] = useState([]); // Stores graph data
  const [selectedNode, setSelectedNode] = useState(null); // Tracks selected node
  const [chunkDict, setChunkDict] = useState({}); // Stores chunk data
  const [isFormalismView, setIsFormalismView] = useState(false); // stores layout state: formalism or browsability
  const [selectedFormalism, setSelectedFormalism] = useState(null); // stores selected formalism
  const [formalismData, setFormalismData] = useState({}); // Stores Formalism data
  const [selectedLoopyURL, setSelectedLoopyURL] = useState(""); // Stores Loopy URL
  // const [message, setMessage] = useState(""); // message for saving conversation
  const [isFullScreen, setIsFullScreen] = useState(false); // full screen status
  const [conversationName, setConversationName] = useState(""); // Stores conversation name for export

const { conversationId } = useParams();

const navigate = useNavigate();

const API_URL = import.meta.env.VITE_API_URL || "";

useEffect(() => {
  if (!conversationId) return;

  // Load conversation data
  fetch(`${API_URL}/conversations/${conversationId}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.graph_data) setGraphData(data.graph_data);
      if (data.chunk_dict) setChunkDict(data.chunk_dict);
    })
    .catch((err) => {
      console.error("Failed to load conversation:", err);
    });

  // Load conversation metadata for name
  fetch(`${API_URL}/conversations/`)
    .then((res) => res.json())
    .then((conversations) => {
      const conversation = conversations.find((c) => c.id === conversationId);
      if (conversation) {
        setConversationName(conversation.file_name);
      }
    })
    .catch((err) => {
      console.error("Failed to load conversation metadata:", err);
    });
}, [conversationId]);

useEffect(() => {
  setIsFullScreen(true); // Trigger fullscreen on load
}, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="w-full px-4 py-4 bg-transparent flex flex-row justify-between items-start md:grid md:grid-cols-3 md:items-center gap-2">
        {/* Left: Back Button & Analysis Menu */}
        <div className="w-full md:w-auto flex justify-start gap-2">
          <button
            onClick={() => navigate("/browse")}
            className="px-4 py-2 h-10 bg-white text-blue-600 font-semibold rounded-lg shadow hover:bg-blue-100 transition text-sm md:text-base"
          >
            ⬅ Back
          </button>

          {/* Analysis Dropdown */}
          <div className="relative group">
            <button
              className="px-4 py-2 h-10 bg-purple-500 text-white font-semibold rounded-lg shadow hover:bg-purple-600 transition text-sm md:text-base"
            >
              Analysis 📊
            </button>

            {/* Dropdown Menu */}
            <div className="absolute left-0 mt-2 w-56 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="py-2">
                <button
                  onClick={() => navigate(`/analytics/${conversationId}`)}
                  className="w-full text-left px-4 py-2 text-gray-700 hover:bg-purple-50 hover:text-purple-600 transition"
                >
                  📈 Speaker Analytics
                </button>
                <button
                  onClick={() => navigate(`/edit-history/${conversationId}`)}
                  className="w-full text-left px-4 py-2 text-gray-700 hover:bg-purple-50 hover:text-purple-600 transition"
                >
                  📝 Edit History
                </button>
                <hr className="my-2 border-gray-200" />
                <div className="px-4 py-1 text-xs font-semibold text-gray-500 uppercase">
                  AI Analysis (Weeks 11-13)
                </div>
                <button
                  onClick={() => navigate(`/simulacra/${conversationId}`)}
                  className="w-full text-left px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition"
                >
                  🎭 Simulacra Levels
                </button>
                <button
                  onClick={() => navigate(`/biases/${conversationId}`)}
                  className="w-full text-left px-4 py-2 text-gray-700 hover:bg-orange-50 hover:text-orange-600 transition"
                >
                  🧠 Cognitive Biases
                </button>
                <button
                  onClick={() => navigate(`/frames/${conversationId}`)}
                  className="w-full text-left px-4 py-2 text-gray-700 hover:bg-green-50 hover:text-green-600 transition"
                >
                  🔍 Implicit Frames
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Center: GenerateFormalism Buttons */}
        <div className="w-full md:w-auto flex justify-end md:justify-center">
          <div className="flex flex-col md:flex-row items-end md:items-center gap-2">
            <GenerateFormalism
              chunkDict={chunkDict}
              graphData={graphData}
              isFormalismView={isFormalismView}
              setIsFormalismView={setIsFormalismView}
              formalismData={formalismData}
              setFormalismData={setFormalismData}
            />
          </div>
        </div>

        {/* Right: Export Actions (desktop only) */}
        {graphData.length > 0 && (
          <div className="hidden md:flex justify-end w-full gap-2">
            <SaveTranscript chunkDict={chunkDict} />
            <ExportCanvas graphData={graphData} fileName={conversationName} />
          </div>
        )}
      </div>

      {!isFormalismView ? (
        // 🔵 Default layout (Structural + Contextual)
        <div className="flex-grow flex flex-col p-6 w-full h-screen space-y-6">
  
          {/* 🟣 Contextual Flow - 3/4 height */}
          <div className="flex-grow-[4] bg-white rounded-lg shadow-lg p-4 w-full overflow-hidden flex flex-col">
            <ContextualGraph
                graphData={graphData}
                chunkDict={chunkDict}
                setGraphData={setGraphData}
                selectedNode={selectedNode}
                setSelectedNode={setSelectedNode}
                isFullScreen={isFullScreen}
                setIsFullScreen={setIsFullScreen}
              />
          </div>

          {/* 🔵 Structural Flow - 1/4 height */}
          <div className="hidden md:flex flex-grow bg-white rounded-lg shadow-lg p-4 w-full overflow-hidden flex flex-col">
            <StructuralGraph
              graphData={graphData}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
            />
          </div>
        </div>
      ) : (
        // 🟣 Formalism layout
        <div className="flex-grow flex flex-col space-y-4 p-4 md:p-6">
          {/* Top Section */}
          <div className="flex flex-col md:flex-row md:space-x-4 space-y-4 md:space-y-0 md:h-2/5">
            {/* Top Left - Formalism List */}
            <div className="w-full md:w-1/2 bg-white rounded-lg shadow-lg p-4">
              <h2 className="text-xl font-bold text-gray-800 text-center mb-2">
                Generated Formalisms
              </h2>
              <FormalismList
                selectedFormalism={selectedFormalism}
                setSelectedFormalism={setSelectedFormalism}
                formalismData={formalismData}
                setFormalismData={setFormalismData}
                setSelectedLoopyURL={setSelectedLoopyURL}
              />
            </div>

            {/* Top Right - Contextual Graph */}
            <div className="hidden md:block w-full md:w-1/2 bg-white rounded-lg shadow-lg p-4">
              <ContextualGraph
                graphData={graphData}
                chunkDict={chunkDict}
                setGraphData={setGraphData}
                selectedNode={selectedNode}
                setSelectedNode={setSelectedNode}
                isFullScreen={isFullScreen}
                setIsFullScreen={setIsFullScreen}
              />
            </div>
          </div>

          {/* Bottom - Canvas */}
          <div className="bg-white rounded-lg shadow-lg p-4 flex flex-col flex-grow">
            <h2 className="text-xl font-bold text-gray-800 text-center mb-2">
              Formalism Model Diagram
            </h2>

            <div className="flex-1 flex items-center justify-center">
              <button
                onClick={() => {
                  const url = selectedLoopyURL || "https://ncase.me/loopy/";
                  window.open(url, "_blank");
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-colors"
              >
                {selectedLoopyURL ? "View Model" : "Open Loopy Editor"}
              </button>
            </div>
          </div>
        </div>
      )}

      {!isFormalismView && (
        <>

          {/* Legend */}
          <div className="hidden md:block absolute bottom-4 right-4">
            <Legend />
          </div>
        </>
      )}
    </div>
  );
}
