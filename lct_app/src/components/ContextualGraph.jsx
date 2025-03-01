import { useState, useMemo, useEffect } from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import dagre from "dagre"; // Import Dagre for auto-layout
import "reactflow/dist/style.css";

export default function ContextualGraph({ graphData, selectedNode, setSelectedNode }) {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [showContext, setShowContext] = useState(false);


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

    const edges = jsonData.flatMap((item) =>
        Object.keys(item.contextual_relation || {}).map((relatedNode) => ({
          id: `e-${relatedNode}-${item.node_name}`,
          source: relatedNode,
          target: item.node_name,
          animated: true,
          style: {
            stroke: selectedNode === item.node_name ? "#ff8800" : "#3f51b5",
            strokeWidth: selectedNode === item.node_name ? 3.5 : 2,
            opacity: selectedNode === item.node_name ? 1 : 0.6,
            transition: "all 0.3s ease-in-out",
          },
          markerEnd: {
            type: "arrowclosed",
            width: 10,
            height: 10,
            color: selectedNode === item.node_name ? "#ff8800" : "#3f51b5",
          },
        }))
      );

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
        <h2 className="text-lg font-semibold text-center flex-grow">Contextual Flow</h2>

        {/* Show Details Button */}
        <button 
            className="px-4 py-2 bg-green-100 text-black rounded-lg shadow-md hover:bg-green-200 active:scale-95 transition" 
            onClick={() => setShowContext(!showContext)}
        >
            whats the context? 🕵️‍♂️
        </button>

        {/* Fullscreen Toggle Button */}
        <button
          className="px-4 py-2 bg-blue-100 text-white rounded-lg shadow-md hover:bg-blue-200 active:scale-95 transition"
          onClick={() => setIsFullScreen(!isFullScreen)}
        >
          {isFullScreen ? "❌" : "🔎"}
        </button>
      </div>

      {/* Context Card */}
      {showContext && selectedNode && (
      <div className="p-4 border rounded-lg bg-green-100 shadow-md mb-2">
        <h3 className="font-semibold text-black">Context for: {selectedNode}</h3>

        <p className="text-sm text-black">
          <strong>Summary:</strong> {jsonData.find(node => node.node_name === selectedNode)?.summary || "No summary available"}
        </p>

        <h4 className="font-semibold mt-2 text-black">Context drawn from:</h4>
        <ul className="list-disc pl-4">
          {Object.entries(jsonData.find(node => node.node_name === selectedNode)?.contextual_relation || {}).map(([key, value]) => (
            <li key={key} className="text-sm text-black">
              <strong>{key}:</strong> {value}
            </li>
          ))}
        </ul>
      </div>
    )}
      
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