import { useState } from "react";
import PropTypes from "prop-types";
import LoopyEditor from "./LoopyEditor";
import MathProof from "./MathProof";

export default function FormalismCanvas({ selectedLoopyURL, selectedFormalismProof }) {
  const [showMathProof, setShowMathProof] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 flex flex-col flex-grow min-h-0">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          {showMathProof ? "Mathematical Proof" : "Formalism Model Diagram"}
        </h2>
        
        {/* Toggle Slider */}
        <div className="flex items-center space-x-3">
          <span className={`text-sm font-medium transition-colors ${
            !showMathProof ? "text-blue-600" : "text-gray-500"
          }`}>
            Causal Loop Diagrams
          </span>
          <button
            onClick={() => setShowMathProof(!showMathProof)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              showMathProof ? "bg-blue-600" : "bg-gray-300"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform ${
                showMathProof ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
          <span className={`text-sm font-medium transition-colors ${
            showMathProof ? "text-blue-600" : "text-gray-500"
          }`}>
            Formal Proofs
          </span>
        </div>
      </div>

      {showMathProof ? (
        <MathProof selectedFormalismProof={selectedFormalismProof} />
      ) : (
        <LoopyEditor selectedLoopyURL={selectedLoopyURL} />
      )}
    </div>
  );
}

FormalismCanvas.propTypes = {
  selectedLoopyURL: PropTypes.string,
  selectedFormalismProof: PropTypes.string,
};
