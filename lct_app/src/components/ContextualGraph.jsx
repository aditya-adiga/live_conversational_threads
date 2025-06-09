import { useState, useMemo, useEffect } from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import dagre from "dagre"; // Import Dagre for auto-layout
import "reactflow/dist/style.css";

export default function ContextualGraph({
  graphData,
  setGraphData,
  selectedNode,
  setSelectedNode,
}) {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [showContext, setShowContext] = useState(false);

  const latestChunk = graphData?.[graphData.length - 1] || [];
  // const jsonData = latestChunk.existing_json || [];

  // logging
  useEffect(() => {
    console.log("Full Graph Data(contextual):", graphData);
    console.log("Latest Chunk Data(contextual):", latestChunk);
    // console.log("Extracted JSON Data:", jsonData);
  }, [graphData]);

  // set context from outside
  useEffect(() => {
    if (!selectedNode) {
      setShowContext(false); // Hide context if selection is cleared elsewhere
    }
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

        const isLinkedEdge =
          item.linked_nodes.includes(relatedNode) ||
          (relatedNodeData?.linked_nodes || []).includes(item.node_name); // Check if either node in the edge is in linked_nodes

        const isFormalismEdge =
          isLinkedEdge &&
          (item.is_contextual_progress ||
            relatedNodeData?.is_contextual_progress); // Check if either node in the edge has is_contextual_progress = true

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
      <div className="relative grid grid-cols-1 md:grid-cols-3 gap-2 items-center justify-between mb-2">
      {/* Left Actions */}
      <div className="flex justify-center md:justify-start space-x-2">
        <button
          className={`px-4 py-2 rounded-lg shadow-md transition active:scale-95 ${
            selectedNode
              ? "bg-green-300 hover:bg-green-400"
              : "bg-gray-300 cursor-not-allowed"
          }`}
          onClick={() => toggleNodeProperty("is_contextual_progress")}
          disabled={!selectedNode}
        >
          {latestChunk.find((node) => node.node_name === selectedNode)
            ?.is_contextual_progress
            ? "Unmark contextual progress"
            : "Mark contextual progress"}
        </button>

        <button
          className={`px-4 py-2 rounded-lg shadow-md transition active:scale-95 ${
            selectedNode
              ? "bg-blue-300 hover:bg-blue-400"
              : "bg-gray-300 cursor-not-allowed"
          }`}
          onClick={() => toggleNodeProperty("is_bookmark")}
          disabled={!selectedNode}
        >
          {latestChunk.find((node) => node.node_name === selectedNode)
            ?.is_bookmark
            ? "Remove Bookmark"
            : "Create Bookmark"}
        </button>
      </div>

      {/* Center Title */}
      <div className="flex justify-center">
      <h2 className="text-lg md:text-xl font-bold text-gray-800 text-center">
        Thematic Flow of Conversation
      </h2>
      </div>

      {/* Right Actions */}
      <div className="flex justify-center md:justify-end space-x-2">
        <button
          className={`px-4 py-2 rounded-lg shadow-md transition active:scale-95 ${
            latestChunk.length > 0 && selectedNode
              ? "bg-yellow-300 hover:bg-yellow-400"
              : "bg-gray-300 cursor-not-allowed"
          }`}
          onClick={() =>
            latestChunk.length > 0 &&
            selectedNode &&
            setShowContext(!showContext)
          }
          disabled={latestChunk.length === 0 || !selectedNode}
        >
          {showContext ? "Hide context" : "What's the context?"}
        </button>

        <button
          className="px-4 py-2 bg-blue-100 text-white rounded-lg shadow-md hover:bg-blue-200 active:scale-95 transition"
          onClick={() => setIsFullScreen(!isFullScreen)}
        >
          {isFullScreen ? "❌" : "🔎"}
        </button>
      </div>
    </div>

      {/* Context Card */}
      {showContext && selectedNode && (
        <div className="p-4 border rounded-lg bg-yellow-100 shadow-md mb-2 z-20 max-h-[200px] overflow-y-auto">
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

      <div className="flex-grow border rounded-lg overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={(_, node) =>
            setSelectedNode((prevSelected) => {
              const isDeselecting = prevSelected === node.id;
              if (isDeselecting) setShowContext(false); // Reset context on deselect
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
