import { useState, useEffect } from "react";

export default function FormalismList({
  selectedFormalism,
  setSelectedFormalism,
  formalismData,
  setSelectedLoopyURL,
  setSelectedFormalismProof,
}) {
  const [formalisms, setFormalisms] = useState([]);

  useEffect(() => {
    if (formalismData && formalismData.formalism_data) {
      // Convert the object to an array of values and extract the formalism_node
      const nodes = Object.values(formalismData.formalism_data).map(
        (item) => item.formalism_node
      );
      setFormalisms(nodes);
    }
  }, [formalismData]);

  const handleSelectFormalism = (item) => {
    setSelectedFormalism(item);

    // Find the corresponding formalism graph URL
    const selectedItem = Object.values(formalismData.formalism_data).find(
      (data) => data.formalism_node === item
    );

    // If found, send the loopy URL and formalism proof to the parent
    if (selectedItem) {
      setSelectedLoopyURL(selectedItem.formalism_graph_url);
      setSelectedFormalismProof(selectedItem.formal_proof);
    }
  };

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
            onClick={() => handleSelectFormalism(item)}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
