import { useState } from "react";
import { useNavigate } from "react-router-dom";
// import Input from "./components/Input";
import AudioInput from "../components/AudioInput";
import StructuralGraph from "../components/StructuralGraph";
import ContextualGraph from "../components/ContextualGraph";
import SaveJson from "../components/SaveJson";
import SaveTranscript from "../components/SaveTranscript";
import Legend from "../components/Legend";
import GenerateFormalism from "../components/GenerateFormalism";
import FormalismList from "../components/FormalismList";

export default function NewConversation() {
  const [graphData, setGraphData] = useState([]); // Stores graph data
  const [selectedNode, setSelectedNode] = useState(null); // Tracks selected node
  const [chunkDict, setChunkDict] = useState({}); // Stores chunk data
  const [isFormalismView, setIsFormalismView] = useState(false); // stores layout state: formalism or browsability
  const [selectedFormalism, setSelectedFormalism] = useState(null); // stores selected formalism
  const [formalismData, setFormalismData] = useState({}); // Stores Formalism data
  const [selectedLoopyURL, setSelectedLoopyURL] = useState(""); // Stores Loopy URL
  const [message, setMessage] = useState(""); // message for saving conversation
  
  const [conversationId, setConversationId] = useState(() => {
    return crypto.randomUUID(); // uuid for conversation
  });

  // Handles streamed JSON data
  const handleDataReceived = (newData) => {
    setGraphData(newData);
  };

  // Handles received chunks
  const handleChunksReceived = (chunks) => {
    setChunkDict(chunks);
  };

  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="relative text-center p-6">
        <button
          onClick={() => navigate("/")}
          className="absolute left-6 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-white text-blue-600 font-semibold rounded-lg shadow hover:bg-blue-100 transition"
        >
          ⬅ Back
        </button>
        <h1 className="text-4xl font-bold">Live Conversational Threads</h1>
      </div>

      {!isFormalismView ? (
        // 🔵 Default layout (Structural + Contextual)
        <div className="flex-grow flex flex-col p-6 w-full h-screen space-y-6">
  
          {/* 🟣 Contextual Flow - 3/4 height */}
          <div className="flex-grow-[4] bg-white rounded-lg shadow-lg p-4 w-full overflow-hidden flex flex-col">
            <ContextualGraph
              graphData={graphData}
              setGraphData={setGraphData}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
            />
          </div>

          {/* 🔵 Structural Flow - 1/4 height */}
          <div className="flex-grow bg-white rounded-lg shadow-lg p-4 w-full overflow-hidden flex flex-col">
            <StructuralGraph
              graphData={graphData}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
            />
          </div>
        </div>
      ) : (
        // 🟣 Formalism layout
        <div className="flex-grow flex flex-col space-y-4 p-6">
          <div className="flex space-x-4 h-2/5">
            {/* Top Left - List of Formalism Options */}
            <div className="w-1/2 bg-white rounded-lg shadow-lg p-4">
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

            {/* Top Right - Contextual Flow */}
            <div className="w-1/2 bg-white rounded-lg shadow-lg p-4">
              <ContextualGraph
                graphData={graphData}
                setGraphData={setGraphData}
                selectedNode={selectedNode}
                setSelectedNode={setSelectedNode}
              />
            </div>
          </div>

          {/* Bottom - Canvas */}
          <div className="h-3/5 bg-white rounded-lg shadow-lg p-4 flex flex-col">
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

      {/* GenerateFormalism Section */}
      <div className="sticky bottom-0 w-full p-4 z-10">
        <GenerateFormalism
          chunkDict={chunkDict}
          graphData={graphData}
          isFormalismView={isFormalismView}
          setIsFormalismView={setIsFormalismView}
          formalismData={formalismData}
          setFormalismData={setFormalismData}
        />
      </div>

      {!isFormalismView && (
        <>
          {/* Audio Input Section */}
          <div className="sticky bottom-0 w-full p-4 flex justify-center z-20">
          <AudioInput
            onDataReceived={handleDataReceived}
            onChunksReceived={handleChunksReceived}
            chunkDict={chunkDict}
            graphData={graphData}
            conversationId={conversationId}
            setMessage={setMessage}
            message={message}
          />
          </div>

          {/* Save Transcript Button */}
          {graphData.length > 0 && (
            <div className="absolute top-4 right-4">
              {/* <SaveJson chunkDict={chunkDict} graphData={graphData} /> */}
              <SaveTranscript chunkDict={chunkDict} />
            </div>
          )}

          {/* Save Transcript Button Below Audio Input */}
          {graphData.length > 0 && (
            <div className="sticky bottom-2 mt-2 w-full flex justify-center z-20">
              <SaveJson
                chunkDict={chunkDict}
                graphData={graphData}
                conversationId={conversationId}
                setMessage={setMessage}
                message={message}
              />
            </div>
          )}

          {/* Legend */}
          <div className="absolute bottom-4 right-4">
            <Legend />
          </div>
        </>
      )}
    </div>
  );
}
