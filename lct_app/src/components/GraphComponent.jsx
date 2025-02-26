import React from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import "reactflow/dist/style.css";

export default function GraphComponent() {
  // Define nodes
  const nodes = [
    { id: "1", data: { label: "Start" }, position: { x: 100, y: 100 } },
    { id: "2", data: { label: "Process" }, position: { x: 250, y: 200 } },
    { id: "3", data: { label: "End" }, position: { x: 400, y: 100 } },
  ];

  // Define directed edges
  const edges = [
    { id: "e1-2", source: "1", target: "2", animated: true },
    { id: "e2-3", source: "2", target: "3", animated: true },
  ];

  return (
    <div className="w-full h-[500px] bg-white shadow-lg rounded-lg p-4">
      <h2 className="text-center text-lg font-semibold mb-2">Directed Graph</h2>
      <div className="w-full h-96 border rounded-lg">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}
