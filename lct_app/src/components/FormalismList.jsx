import { useState } from "react";

export default function FormalismList({
  selectedFormalism,
  setSelectedFormalism,
}) {
  const formalisms = [
    "Petri Nets",
    "Statecharts",
    "Process Algebra",
    "Temporal Logic",
    "Finite State Machines",
    "Category Theory",
  ];

  return (
    <div className="h-[calc(100%-40px)] overflow-y-auto p-4 bg-white rounded-lg shadow">
      <ul className="space-y-2">
        {formalisms.map((item) => (
          <li
            key={item}
            className={`p-3 rounded-lg cursor-pointer transition-colors ${
              selectedFormalism === item
                ? "bg-green-100 text-green-700 font-semibold"
                : "bg-gray-100 hover:bg-gray-200 text-gray-700"
            }`}
            onClick={() => setSelectedFormalism(item)}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
