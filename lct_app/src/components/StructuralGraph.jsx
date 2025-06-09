import { useState, useMemo, useEffect } from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import dagre from "dagre"; // Import Dagre for auto-layout
import "reactflow/dist/style.css";

export default function StructuralGraph({
  graphData,
  selectedNode,
  setSelectedNode,
}) {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const latestChunk = graphData?.[graphData.length - 1] || [];
  // const jsonData = latestChunk.existing_json || [];

  useEffect(() => {
    console.log("Full Graph Data(Structural):", graphData);
    console.log("Latest Chunk Data(Structural):", latestChunk);
    // console.log("Extracted JSON Data:", jsonData);
  }, [graphData]);

  // Dagre Graph Configuration
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setGraph({ rankdir: "LR", nodesep: 50, ranksep: 100 }); // Left-to-right layout
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Generate nodes and edges
  const { nodes, edges } = useMemo(() => {
    const nodes = latestChunk.map((item) => {
      let background, border, boxShadow;

      if (item.is_contextual_progress) {
        background = "#ccffcc"; // Light Green
        border = "2px solid #33cc33"; // Green Border
        boxShadow = "0px 0px 10px rgba(51, 204, 51, 0.6)"; // Green Glow
      } else if (item.is_bookmark) {
        background = "#cce5ff"; // Light Blue
        border = "2px solid #3399ff"; // Blue Border
        boxShadow = "0px 0px 10px rgba(51, 153, 255, 0.6)"; // Blue Glow
      } else if (selectedNode === item.node_name) {
        background = "#ffcc00"; // Yellow for selected
        border = "3px solid #ff8800"; // Orange Border
        boxShadow = "0px 0px 15px rgba(255, 136, 0, 0.8)"; // Orange Glow
      } else {
        background = "white";
        border = "1px solid #ccc";
        boxShadow = "none";
      }

      return {
        id: item.node_name,
        data: { label: item.node_name },
        position: { x: 0, y: 0 }, // Dagre will handle positioning
        style: {
          background,
          border,
          boxShadow,
          transition: "all 0.3s ease-in-out",
        },
      };
    });

    const edges = latestChunk
      .filter((item) => item.predecessor)
      .map((item) => {
        const predecessorNode = latestChunk.find(
          (n) => n.node_name === item.predecessor
        );

        const isFormalismEdge =
          item.is_contextual_progress ||
          predecessorNode?.is_contextual_progress;

        return {
          id: `e-${item.predecessor}-${item.node_name}`,
          source: item.predecessor,
          target: item.node_name,
          animated: true,
          style: {
            stroke:
              selectedNode === item.node_name
                ? "#ff8800"
                : isFormalismEdge
                ? "#33cc33"
                : "#898989",
            strokeWidth:
              selectedNode === item.node_name ||
              selectedNode === item.predecessor ||
              isFormalismEdge
                ? 3.5
                : 2,
            opacity:
              selectedNode === item.node_name ||
              selectedNode === item.predecessor ||
              isFormalismEdge
                ? 1
                : 0.6,
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
      });

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
          ? "fixed inset-0 w-screen h-screen z-50" // "absolute top-0 left-0 w-full h-full z-50"
          : "w-full h-full" //[calc(100%-40px)]"
      }`}
    >
      <div className="relative flex items-center justify-center mb-2">
        
      <h2 className="mx-auto text-xl font-bold text-gray-800 text-center">
              Chronological Flow of Conversation
            </h2>
      </div>

      <div className="flex-grow border rounded-lg overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={(_, node) =>
            setSelectedNode((prevSelected) =>
              prevSelected === node.id ? null : node.id
            )
          } // Sync selection
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}
