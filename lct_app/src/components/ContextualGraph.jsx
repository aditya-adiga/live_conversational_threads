import { useState, useMemo, useEffect } from "react";
import PropTypes from "prop-types";
import ReactFlow, { Controls, Background } from "reactflow";
import dagre from "dagre"; // Import Dagre for auto-layout
import "reactflow/dist/style.css";

export default function ContextualGraph({
  graphData,
  chunkDict,
  setGraphData,
  selectedNode,
  setSelectedNode,
  isFullScreen,
  setIsFullScreen,
}) {
  // const [isFullScreen, setIsFullScreen] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [isClaimsPanelOpen, setIsClaimsPanelOpen] = useState(false);
  const [factCheckResults, setFactCheckResults] = useState(null);
  const [isFactChecking, setIsFactChecking] = useState(false);

  const latestChunk = graphData?.[graphData.length - 1] || [];

  const selectedNodeData = useMemo(() => {
    if (!selectedNode) return null;
    return latestChunk.find((node) => node.node_name === selectedNode);
  }, [selectedNode, latestChunk]);

  const selectedNodeClaims = selectedNodeData?.claims || [];

  // logging
  useEffect(() => {
    console.log("Full Graph Data(contextual):", graphData);
    console.log("Latest Chunk Data(contextual):", latestChunk);
  }, [graphData]);

  const handleFactCheck = async () => {
    if (selectedNodeClaims.length === 0) return;

    // Check for existing results first
    if (selectedNodeData?.claims_checked) {
      setFactCheckResults(selectedNodeData.claims_checked);
      return;
    }

    setIsFactChecking(true);
    setFactCheckResults(null); // Clear previous results

    try {
      const API_URL = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${API_URL}/fact_check_claims/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claims: selectedNodeClaims }),
      });

      if (!response.ok) {
        throw new Error(`Fact-check failed: ${response.statusText}`);
      }

      const data = await response.json();
      setFactCheckResults(data.claims);

      // Update graphData to include the checked claims
      const newGraphData = graphData.map((chunk) =>
        chunk.map((node) =>
          node.node_name === selectedNode
            ? { ...node, claims_checked: data.claims }
            : node
        )
      );
      setGraphData(newGraphData);
    } catch (error) {
      console.error("Error during fact-checking:", error);
    } finally {
      setIsFactChecking(false);
    }
  };

  // set context from outside
  useEffect(() => {
    if (!selectedNode) {
      setShowContext(false); 
      setShowTranscript(false);
      setIsClaimsPanelOpen(false);
    }
    setFactCheckResults(null);
  }, [selectedNode]);

  // toggle button functionality
  const toggleNodeProperty = (property) => {
    if (!selectedNode) return;

    setGraphData((prevData) =>
      prevData.map((chunk) =>
        chunk.map((node) =>
          node.node_name === selectedNode
            ? { ...node, [property]: !node[property] } // Toggle property
            : node
        )
      )
    );
  };

  // Dagre Graph Configuration
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setGraph({ rankdir: "LR", nodesep: 50, ranksep: 100 }); // Left-to-right layout
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Generate nodes and edges
  const { nodes, edges } = useMemo(() => {
    const nodes = latestChunk.map((item) => {
      let background, border, boxShadow;

      if (item.is_contextual_progress) {
        // Highest priority: contextual progress
        background = "#ccffcc"; // Light Green
        border = "2px solid #33cc33"; // Green Border
        boxShadow = "0px 0px 10px rgba(51, 204, 51, 0.6)"; // Green Glow
      } else if (item.is_bookmark) {
        // Second priority: Bookmark
        background = "#cce5ff"; // Light Blue
        border = "2px solid #3399ff"; // Blue Border
        boxShadow = "0px 0px 10px rgba(51, 153, 255, 0.6)"; // Blue Glow
      } else if (selectedNode === item.node_name) {
        // Last priority: Selected Node
        background = "#ffcc00"; // Yellow
        border = "3px solid #ff8800"; // Orange Border
        boxShadow = "0px 0px 15px rgba(255, 136, 0, 0.8)"; // Orange Glow
      } else {
        // Default Style
        background = "white";
        border = "1px solid #ccc";
        boxShadow = "none";
      }

      return {
        id: item.node_name,
        data: { label: item.node_name },
        position: { x: 0, y: 0 }, // Dagre handles positioning
        style: {
          background,
          border,
          boxShadow,
          transition: "all 0.3s ease-in-out",
        },
      };
    });
    const edges = latestChunk.flatMap((item) =>
      Object.keys(item.contextual_relation || {}).map((relatedNode) => {
        const relatedNodeData = latestChunk.find(
          (n) => n.node_name === relatedNode
        );

        const isRelatedEdge = Object.keys(
          relatedNodeData?.contextual_relation || {}
        ).includes(item.node_name);

        const isFormalismEdge =
        isRelatedEdge &&
          (item.is_contextual_progress ||
            relatedNodeData?.is_contextual_progress);

        return {
          id: `e-${relatedNode}-${item.node_name}`,
          source: relatedNode,
          target: item.node_name,
          animated: true,
          style: {
            stroke:
              selectedNode === item.node_name
                ? "#ff8800" // Orange for selected node edges
                : isFormalismEdge
                ? "#33cc33" // Green for formalism-related edges
                : "#898989", // Default blue
            strokeWidth:
              selectedNode === item.node_name || isFormalismEdge ? 3.5 : 2,
            opacity:
              selectedNode === item.node_name || isFormalismEdge ? 1 : 0.6,
            transition: "all 0.3s ease-in-out",
          },
          markerEnd: {
            type: "arrowclosed",
            width: 10,
            height: 10,
            color:
              selectedNode === item.node_name
                ? "#ff8800"
                : isFormalismEdge
                ? "#33cc33"
                : "#898989",
          },
        };
      })
    );

    // Add nodes & edges to Dagre graph
    nodes.forEach((node) =>
      dagreGraph.setNode(node.id, { width: 180, height: 50 })
    );
    edges.forEach((edge) => dagreGraph.setEdge(edge.source, edge.target));

    dagre.layout(dagreGraph); // Apply layout

    // Update positions from Dagre
    const positionedNodes = nodes.map((node) => ({
      ...node,
      position: dagreGraph.node(node.id),
    }));

    return { nodes: positionedNodes, edges };
  }, [latestChunk, selectedNode]);

  return (
    <div
      className={`flex flex-col bg-white shadow-lg rounded-lg p-4 transition-all duration-300 ${
        isFullScreen
          ? "fixed top-0 left-0 right-0 bottom-0 w-screen h-screen z-50 overflow-hidden" // "absolute top-0 left-0 w-full h-full z-50"
          : "w-full h-full" // [calc(100%-40px)]"
      }`}
    >
      <div className="flex justify-between items-center mb-2 w-full">
        {/* Left: Claims Button */}
        <button
          className={`px-4 py-2 rounded-lg shadow-md transition active:scale-95 ${
            selectedNodeClaims.length > 0
              ? "bg-indigo-300 hover:bg-indigo-400"
              : "bg-gray-300 cursor-not-allowed"
          }`}
          onClick={() => setIsClaimsPanelOpen(true)}
          disabled={selectedNodeClaims.length === 0}
        >
          Claims
        </button>
        

        {/* Middle: Context Button */}
        <button
          className={`px-4 py-2 rounded-lg shadow-md transition active:scale-95 ${
            latestChunk.length > 0 && selectedNode
              ? "bg-yellow-300 hover:bg-yellow-400"
              : "bg-gray-300 cursor-not-allowed"
          }`}
          onClick={() => {
            if (latestChunk.length > 0 && selectedNode) {
              const nextState = !showContext;
              setShowContext(nextState);
              if (!nextState) {
                setShowTranscript(false);
              }
            }
          }}

          disabled={latestChunk.length === 0 || !selectedNode}
        >
          {showContext ? "Hide  Context" : "Context"}
        </button>

        {/* Right: Fullscreen Button */}
        <button
          className="px-4 py-2 bg-blue-100 text-white rounded-lg shadow-md hover:bg-blue-200 active:scale-95 transition"
          onClick={() => setIsFullScreen(!isFullScreen)}
        >
          {isFullScreen ? "🡼" : "⛶"}
        </button>
      </div>

      {/* Context Card */}
      {showContext && selectedNode && (
        <div className="p-4 border rounded-lg bg-yellow-100 shadow-md mb-2 z-20 max-h-[200px] overflow-y-auto">
            <div className="mt-4 flex flex-wrap justify-center gap-2">
            <button
              className="px-4 py-2 rounded-lg shadow-md bg-green-300 hover:bg-green-400"
              onClick={() => toggleNodeProperty("is_contextual_progress")}
            >
              {latestChunk.find((node) => node.node_name === selectedNode)
                ?.is_contextual_progress
                ? "Unmark contextual progress"
                : "Mark contextual progress"}
            </button>

            <button
              className="px-4 py-2 rounded-lg shadow-md bg-blue-300 hover:bg-blue-400"
              onClick={() => toggleNodeProperty("is_bookmark")}
            >
              {latestChunk.find((node) => node.node_name === selectedNode)
                ?.is_bookmark
                ? "Remove Bookmark"
                : "Create Bookmark"}
            </button>

            <button
              className="px-4 py-2 rounded-lg shadow-md bg-purple-300 hover:bg-purple-400"
              onClick={() => setShowTranscript(!showTranscript)}
            >
              {showTranscript ? "Hide transcript" : "View transcript"}
            </button>
          </div>
          
          <h3 className="font-semibold text-black">
            Context for: {selectedNode}
          </h3>

          <p className="text-sm text-black">
            <strong>Summary:</strong>{" "}
            {latestChunk.find((node) => node.node_name === selectedNode)
              ?.summary || "No summary available"}
          </p>

          {latestChunk.find((node) => node.node_name === selectedNode)
            ?.contextual_relation &&
            Object.keys(
              latestChunk.find((node) => node.node_name === selectedNode)
                ?.contextual_relation
            ).length > 0 && (
              <>
                <h4 className="font-semibold mt-2 text-black">
                  Context drawn from:
                </h4>
                <ul className="list-disc pl-4">
                  {Object.entries(
                    latestChunk.find((node) => node.node_name === selectedNode)
                      ?.contextual_relation
                  ).map(([key, value]) => (
                    <li key={key} className="text-sm text-black">
                      <strong>{key}:</strong> {value}
                    </li>
                  ))}
                </ul>
              </>
            )}
        </div>
      )}

      {/* Transcript Card */}
      {showTranscript && selectedNode && (() => {
        const selectedNodeData = latestChunk.find(
          (node) => node.node_name === selectedNode
        );
        const chunkId = selectedNodeData?.chunk_id;
        const transcript = chunkDict?.[chunkId] || "Transcript not available";

        return (
          <div className="p-4 border rounded-lg bg-purple-100 shadow-md mb-2 z-20 max-h-[200px] overflow-y-auto">
            <h3 className="font-semibold text-black">
              Transcript for: {selectedNode}
            </h3>
            <p className="text-sm text-black whitespace-pre-wrap">
              {transcript}
            </p>
          </div>
        );
      })()}

      {/* Claims Panel */}
      <div
        className={`
          fixed top-0 right-0 h-full bg-indigo-100 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out
          p-4 sm:p-6 overflow-y-auto w-full sm:w-1/2 lg:w-1/3
          ${isClaimsPanelOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
          <button
              onClick={() => setIsClaimsPanelOpen(false)}
              className="absolute top-4 right-4 text-gray-600 hover:text-gray-900 text-2xl"
          >
              &times;
          </button>
          <h2 className="text-xl font-bold mb-4 text-indigo-900">Claims for: {selectedNode}</h2>
          
          {selectedNodeClaims.length > 0 ? (
              <>
                  <ul className="space-y-2 mb-4 list-disc pl-5">
                      {selectedNodeClaims.map((claim, index) => (
                          <li key={index} className="text-sm text-gray-800">{claim}</li>
                      ))}
                  </ul>
                  <button
                      onClick={handleFactCheck}
                      disabled={isFactChecking}
                      className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg shadow hover:bg-blue-600 disabled:bg-blue-300"
                  >
                      {isFactChecking ? "Fact-Checking..." : `Fact Check Claims for ${selectedNode}`}
                  </button>
              </>
          ) : (
              <p>No claims were found for this node.</p>
          )}

          {isFactChecking && !factCheckResults && <p className="mt-4 text-center">Loading results...</p>}

          {factCheckResults && (
              <div className="mt-6 space-y-4">
                  <h3 className="text-lg font-bold text-indigo-800 border-b pb-2 mb-2">Fact-Check Results</h3>
                  {factCheckResults.map((result, index) => (
                      <div key={index} className="p-4 rounded-lg bg-white shadow">
                          <p className="font-semibold text-gray-800">{result.claim}</p>
                          <p className={`font-bold text-sm ${
                              result.verdict === 'True' ? 'text-green-700' : 
                              result.verdict === 'False' ? 'text-red-700' : 'text-yellow-600'
                          }`}>Verdict: {result.verdict}</p>
                          <p className="mt-2 text-sm text-gray-600">{result.explanation}</p>
                          {result.citations.length > 0 && (
                              <div className="mt-2">
                                  <h4 className="font-semibold text-xs text-gray-500 uppercase tracking-wider">Sources:</h4>
                                  <ul className="list-disc pl-5 space-y-1 mt-1">
                                      {result.citations.map((cite, i) => (
                                          <li key={i} className="text-sm">
                                              <a href={cite.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                                  {cite.title}
                                              </a>
                                          </li>
                                      ))}
                                  </ul>
                              </div>
                          )}
                      </div>
                  ))}
              </div>
          )}
      </div>

      <div className="flex-grow border rounded-lg overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
           // 🔍 Zoom Controls
          zoomOnPinch={true}
          zoomOnScroll={true}

          // 🖱️ Pan Controls
          panOnDrag={true} 
          panOnScroll={false}
          onNodeClick={(_, node) =>
          setSelectedNode((prevSelected) => {
            const isDeselecting = prevSelected === node.id;
            if (isDeselecting) setShowContext(false); // Reset context on deselect
            if (isDeselecting) setShowTranscript(false); // Reset context on deselect
            return isDeselecting ? null : node.id;
          })
          } // Sync selection
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}

ContextualGraph.propTypes = {
  graphData: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        node_name: PropTypes.string.isRequired,
        claims: PropTypes.arrayOf(PropTypes.string),
        is_contextual_progress: PropTypes.bool,
        is_bookmark: PropTypes.bool,
        summary: PropTypes.string,
        contextual_relation: PropTypes.object,
        chunk_id: PropTypes.string,
        conversation_id: PropTypes.string,
        claims_checked: PropTypes.array,
      })
    )
  ),
  chunkDict: PropTypes.object,
  setGraphData: PropTypes.func.isRequired,
  selectedNode: PropTypes.string,
  setSelectedNode: PropTypes.func.isRequired,
  isFullScreen: PropTypes.bool.isRequired,
  setIsFullScreen: PropTypes.func.isRequired,
};
