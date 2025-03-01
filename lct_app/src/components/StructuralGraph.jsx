import { useState, useMemo, useEffect } from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import dagre from "dagre"; // Import Dagre for auto-layout
import "reactflow/dist/style.css";

export default function StructuralGraph({ graphData, selectedNode, setSelectedNode }) {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const latestChunk = graphData?.[graphData.length - 1] || {}; 
  const jsonData = latestChunk.existing_json || []; 

  useEffect(() => {
    console.log("Full Graph Data:", graphData);
    console.log("Latest Chunk Data:", latestChunk);
    console.log("Extracted JSON Data:", jsonData);
  }, [graphData]);

  // Dagre Graph Configuration
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setGraph({ rankdir: "LR", nodesep: 50, ranksep: 100 }); // Left-to-right layout
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Generate nodes and edges
  const { nodes, edges } = useMemo(() => {
    const nodes = jsonData.map((item) => ({
      id: item.node_name,
      data: { label: item.node_name },
      position: { x: 0, y: 0 }, // Dagre will handle positioning
      style: {
        background: selectedNode === item.node_name 
          ? "#ffcc00"  // Highlighted node (Yellow)
          : item.is_bookmark 
            ? "#cce5ff"  // Bookmarked node (Light Blue)
            : "white",
        border: selectedNode === item.node_name 
          ? "3px solid #ff8800" 
          : item.is_bookmark 
            ? "2px solid #3399ff"  // Bookmarked node border (Blue)
            : "1px solid #ccc",
        boxShadow: selectedNode === item.node_name 
          ? "0px 0px 15px rgba(255, 136, 0, 0.8)" 
          : item.is_bookmark 
            ? "0px 0px 10px rgba(51, 153, 255, 0.6)"  // Bookmarked node glow
            : "none",
        transition: "all 0.3s ease-in-out",
      },
    }));
    
    const edges = jsonData
      .filter((item) => item.predecessor)
      .map((item) => ({
        id: `e-${item.predecessor}-${item.node_name}`,
        source: item.predecessor,
        target: item.node_name,
        animated: true,
        style: {
          stroke: selectedNode === item.node_name || selectedNode === item.predecessor 
            ? "#ff8800"  // Highlighted edge (Orange)
            : "#3f51b5",  // Default edge (Blue)
          strokeWidth: selectedNode === item.node_name || selectedNode === item.predecessor 
            ? 3.5  // Thicker edge for selected nodes
            : 2,
          transition: "stroke 0.3s ease-in-out",
        },
        markerEnd: { 
          type: "arrowclosed", 
          width: 10, 
          height: 10, 
          color: selectedNode === item.node_name || selectedNode === item.predecessor 
            ? "#ff8800"  // Highlighted arrow
            : "#3f51b5",  // Default arrow
        },
      }));

    // Add nodes & edges to Dagre graph
    nodes.forEach((node) => dagreGraph.setNode(node.id, { width: 180, height: 50 }));
    edges.forEach((edge) => dagreGraph.setEdge(edge.source, edge.target));

    dagre.layout(dagreGraph); // Apply layout

    // Update positions from Dagre
    const positionedNodes = nodes.map((node) => ({
      ...node,
      position: dagreGraph.node(node.id), 
    }));

    return { nodes: positionedNodes, edges };
  }, [jsonData, selectedNode]);

  return (
    <div className={`flex flex-col bg-white shadow-lg rounded-lg p-4 transition-all duration-300 ${
      isFullScreen ? "absolute top-0 left-0 w-full h-full z-50" : "w-full h-[500px]"
    }`}>
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold text-center flex-grow">Structural Flow</h2>

        {/* Fullscreen Toggle Button */}

        <button
          className="px-4 py-2 bg-blue-100 text-white rounded-lg shadow-md hover:bg-blue-200 active:scale-95 transition"
          onClick={() => setIsFullScreen(!isFullScreen)}
        >
          {isFullScreen ? "❌" : "🔎"}
        </button>
        
      </div>
      
      <div className="flex-grow border rounded-lg overflow-hidden">
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          fitView
          onNodeClick={(_, node) => setSelectedNode && setSelectedNode(node.id)} // Sync selection
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}