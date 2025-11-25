import PropTypes from "prop-types";
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
 
 export default function MathProof({ selectedFormalismProof }) {
 
  return (
    <div className="h-96 w-full overflow-y-auto bg-white rounded-lg shadow p-6">
      {selectedFormalismProof ? (
        <div className="prose prose-lg max-w-none text-gray-800 leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {selectedFormalismProof}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <p className="text-lg">Select a formalism to view its mathematical proof</p>
          </div>
        </div>
      )}
    </div>
  );
 }
 
 MathProof.propTypes = {
  selectedFormalismProof: PropTypes.string,
 };

