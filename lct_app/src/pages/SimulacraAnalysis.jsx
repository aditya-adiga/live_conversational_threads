/**
 * Simulacra Analysis Page
 * Week 11: Advanced AI Analysis
 *
 * Displays Simulacra level classification results for conversation nodes
 * Based on Baudrillard's theory of simulation and hyperreality
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  analyzeSimulacraLevels,
  getSimulacraResults,
  getLevelInfo
} from '../services/simulacraApi';

export default function SimulacraAnalysis() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState(null);

  useEffect(() => {
    loadResults();
  }, [conversationId]);

  const loadResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getSimulacraResults(conversationId);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (forceReanalysis = false) => {
    setAnalyzing(true);
    setError(null);

    try {
      const data = await analyzeSimulacraLevels(conversationId, forceReanalysis);
      setResults(data);
      alert(`Analysis complete! Analyzed ${data.analyzed} nodes.`);
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const getFilteredNodes = () => {
    if (!results || !results.nodes) return [];
    if (selectedLevel === null) return results.nodes;
    return results.nodes.filter(node => node.level === selectedLevel);
  };

  const formatConfidence = (confidence) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading Simulacra analysis...</p>
        </div>
      </div>
    );
  }

  const filteredNodes = getFilteredNodes();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <button
              onClick={() => navigate(-1)}
              className="text-blue-600 hover:text-blue-800 mb-2 flex items-center"
            >
              ← Back
            </button>
            <h1 className="text-3xl font-bold text-gray-800">Simulacra Level Analysis</h1>
            <p className="text-gray-600 mt-1">
              Classification based on Baudrillard's theory of simulation and hyperreality
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            {results && results.analyzed > 0 ? (
              <button
                onClick={() => handleAnalyze(true)}
                disabled={analyzing}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:bg-gray-400"
              >
                {analyzing ? 'Re-analyzing...' : 'Re-analyze'}
              </button>
            ) : (
              <button
                onClick={() => handleAnalyze(false)}
                disabled={analyzing}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
              >
                {analyzing ? 'Analyzing...' : 'Run Analysis'}
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-600 underline text-sm mt-2"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Results */}
      {results && results.analyzed > 0 ? (
        <>
          {/* Distribution Cards */}
          <div className="max-w-7xl mx-auto mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Distribution by Level</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(level => {
                const info = getLevelInfo(level);
                const count = results.distribution[level] || 0;
                const percentage = results.total_nodes > 0
                  ? ((count / results.total_nodes) * 100).toFixed(1)
                  : 0;
                const isSelected = selectedLevel === level;

                return (
                  <button
                    key={level}
                    onClick={() => setSelectedLevel(isSelected ? null : level)}
                    className={`${info.bgColor} ${info.borderColor} border-2 rounded-lg p-4 text-left transition hover:shadow-lg ${
                      isSelected ? 'ring-4 ring-blue-300' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-2xl font-bold ${info.color}`}>
                        Level {level}
                      </span>
                      <span className="text-3xl font-bold text-gray-800">{count}</span>
                    </div>
                    <p className={`text-sm font-medium ${info.color} mb-1`}>
                      {info.name}
                    </p>
                    <p className="text-xs text-gray-600 mb-2">
                      {info.description}
                    </p>
                    <div className="mt-3">
                      <div className="bg-white rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full ${info.bgColor.replace('100', '500')}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{percentage}% of nodes</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedLevel && (
              <div className="mt-3 text-center">
                <button
                  onClick={() => setSelectedLevel(null)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Clear filter (showing all nodes)
                </button>
              </div>
            )}
          </div>

          {/* Level Reference Guide */}
          <div className="max-w-7xl mx-auto mb-6">
            <details className="bg-white rounded-lg shadow p-4">
              <summary className="cursor-pointer font-semibold text-gray-800">
                📚 Simulacra Levels Reference Guide
              </summary>
              <div className="mt-4 space-y-4">
                {[1, 2, 3, 4].map(level => {
                  const info = getLevelInfo(level);
                  return (
                    <div key={level} className={`${info.bgColor} ${info.borderColor} border rounded p-3`}>
                      <p className={`font-bold ${info.color} mb-1`}>
                        Level {level}: {info.name}
                      </p>
                      <p className="text-sm text-gray-700 mb-2">{info.description}</p>
                      <p className="text-xs text-gray-600">
                        <span className="font-semibold">Examples:</span>{' '}
                        {info.examples.join(', ')}
                      </p>
                    </div>
                  );
                })}
              </div>
            </details>
          </div>

          {/* Node List */}
          <div className="max-w-7xl mx-auto">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Node Analysis
              {selectedLevel && ` - Level ${selectedLevel} (${filteredNodes.length})`}
            </h2>

            {filteredNodes.length > 0 ? (
              <div className="space-y-4">
                {filteredNodes.map((node) => {
                  const info = getLevelInfo(node.level);

                  return (
                    <div
                      key={node.node_id}
                      className="bg-white rounded-lg shadow hover:shadow-lg transition"
                    >
                      <div className="p-6">
                        {/* Node Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-800 mb-2">
                              {node.node_name}
                            </h3>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-medium px-3 py-1 rounded-full ${info.bgColor} ${info.color}`}>
                                Level {node.level}: {info.name}
                              </span>
                              <span className="text-xs text-gray-500">
                                Confidence: {formatConfidence(node.confidence)}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div className="mb-4">
                          <p className="text-sm font-medium text-gray-700 mb-1">Analysis:</p>
                          <p className="text-sm text-gray-600 bg-gray-50 rounded p-3">
                            {node.reasoning}
                          </p>
                        </div>

                        {/* Examples */}
                        {node.examples && node.examples.length > 0 && (
                          <div>
                            <p className="text-sm font-medium text-gray-700 mb-2">Examples:</p>
                            <ul className="space-y-1">
                              {node.examples.map((example, i) => (
                                <li
                                  key={i}
                                  className={`text-sm ${info.color} ${info.bgColor} rounded p-2`}
                                >
                                  "{example}"
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-gray-500 text-lg">
                  No nodes found for Level {selectedLevel}
                </p>
                <button
                  onClick={() => setSelectedLevel(null)}
                  className="mt-4 text-blue-600 hover:text-blue-800"
                >
                  View all nodes
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        /* No Results State */
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">No Analysis Yet</h2>
            <p className="text-gray-600 mb-6">
              Click "Run Analysis" to classify all conversation nodes by their Simulacra level.
            </p>
            <p className="text-sm text-gray-500 mb-8">
              This will use AI to analyze each node and classify it based on its relationship
              to reality using Baudrillard's 4-level framework.
            </p>
            <button
              onClick={() => handleAnalyze(false)}
              disabled={analyzing}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 text-lg"
            >
              {analyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
