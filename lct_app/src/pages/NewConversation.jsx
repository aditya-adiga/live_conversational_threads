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
  const [fileName, setFileName] = useState(""); //filename for saving conversation
  const [isFullScreen, setIsFullScreen] = useState(false); // full screen status
  
  const [conversationId, setConversationId] = useState(() => {
    return crypto.randomUUID(); // uuid for conversation
  });

  // Handles streamed JSON data
  const handleDataReceived = (newData) => {
    setGraphData((prevGraphData) => {
      // If no previous data, just use new data
      if (!prevGraphData || prevGraphData.length === 0) {
        return newData;
      }

      // Merge new data with existing user annotations
      return mergeGraphDataWithUserAnnotations(prevGraphData, newData);
    });
  };

  // Helper function to preserve user annotations when receiving backend updates
  const mergeGraphDataWithUserAnnotations = (currentData, incomingData) => {
    if (!incomingData || incomingData.length === 0) return currentData;
    
    return incomingData.map((incomingChunk, chunkIndex) => {
      const currentChunk = currentData[chunkIndex] || [];
      
      return incomingChunk.map((incomingNode) => {
        const currentNode = currentChunk.find(node => node.node_name === incomingNode.node_name);
        
        if (currentNode) {
          // Preserve user annotations from current node
          return {
            ...incomingNode,
            is_contextual_progress: currentNode.is_contextual_progress || incomingNode.is_contextual_progress,
            is_bookmark: currentNode.is_bookmark || incomingNode.is_bookmark,
            claims_checked: currentNode.claims_checked || incomingNode.claims_checked,
          };
        }
        
        return incomingNode;
      });
    });
  };

  // Handles received chunks
  const handleChunksReceived = (chunks) => {
    setChunkDict(chunks);
  };

  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="w-full px-4 py-4 bg-transparent flex flex-row justify-between items-start md:grid md:grid-cols-3 md:items-center gap-2">
        {/* Left: Back Button */}
        <div className="w-full md:w-auto flex justify-start">
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 h-10 bg-white text-blue-600 font-semibold rounded-lg shadow hover:bg-blue-100 transition text-sm md:text-base"
          >
            ⬅ Exit
          </button>
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

        {/* Right: Save Transcript (desktop only) */}
        {graphData.length > 0 && (
          <div className="hidden md:flex justify-end w-full">
            <SaveTranscript chunkDict={chunkDict} />
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
      
      {/* Audio Input Section - Always visible */}
      <div className="sticky bottom-0 w-full p-4 flex justify-center z-20">
        <AudioInput
          onDataReceived={handleDataReceived}
          onChunksReceived={handleChunksReceived}
          chunkDict={chunkDict}
          graphData={graphData}
          conversationId={conversationId}
          setConversationId={setConversationId}
          setMessage={setMessage}
          message={message}
          fileName={fileName}
          setFileName={setFileName}
        />
      </div>

          {/* Save Transcript Button Below Audio Input */}
          {graphData.length > 0 && (
            <div className="w-full px-4 mt-4 mb-2 z-20 flex justify-center md:sticky md:bottom-2">
              <SaveJson
                chunkDict={chunkDict}
                graphData={graphData}
                conversationId={conversationId}
                setMessage={setMessage}
                message={message}
                fileName={fileName}
                setFileName={setFileName}
              />
            </div>
          )}

      {/* Legend - Only show in non-formalism view */}
      {!isFormalismView && (
        <div className="hidden md:block absolute bottom-4 right-4">
          <Legend />
        </div>
      )}
    </div>
  );
}
