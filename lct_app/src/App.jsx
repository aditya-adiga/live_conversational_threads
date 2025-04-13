import { useState } from "react";
import Input from "./components/Input";
import StructuralGraph from "./components/StructuralGraph";
import ContextualGraph from "./components/ContextualGraph";
import SaveJson from "./components/SaveJson";
import Legend from "./components/Legend";

export default function App() {
  const [graphData, setGraphData] = useState([]); // Stores graph data
  const [selectedNode, setSelectedNode] = useState(null); // Tracks selected node
  const [chunkDict, setChunkDict] = useState({}); // Stores chunk data

  // Handles streamed JSON data
  const handleDataReceived = (newData) => {
    setGraphData(newData);
  };

  // Handles received chunks
  const handleChunksReceived = (chunks) => {
    setChunkDict(chunks);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="text-center p-6">
        <h1 className="text-4xl font-bold">Live Conversational Threads</h1>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 right-4">
        <Legend />
      </div>

      {/* Graph Section */}
      <div className="flex-grow flex justify-center items-center p-6">
        <div className="flex space-x-7 w-full max-w-15xl">
          {/* Structural Graph */}
          <div className="w-1/3 bg-white rounded-lg shadow-lg p-4">
            <h2 className="text-xl font-bold text-gray-800 text-center mb-2">
              Structural Flow
            </h2>
            <StructuralGraph
              graphData={graphData}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
            />
          </div>

          {/* Contextual Graph */}
          <div className="w-2/3 bg-white rounded-lg shadow-lg p-4">
            <h2 className="text-xl font-bold text-gray-800 text-center mb-2">
              Contextual Flow
            </h2>
            <ContextualGraph
              graphData={graphData}
              setGraphData={setGraphData}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
            />
          </div>
        </div>
      </div>

      {/* Input Section */}
      <div className="sticky bottom-0 w-full shadow-lg p-4">
        <Input
          onChunksReceived={handleChunksReceived}
          onDataReceived={handleDataReceived}
        />
      </div>

      {/* Save Button */}
      {graphData.length > 0 && (
        <div className="absolute top-4 right-4">
          <SaveJson chunkDict={chunkDict} graphData={graphData} />
        </div>
      )}
    </div>
  );
}
