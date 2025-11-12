/**
 * Implicit Frame Analysis Page
 * Week 13: Advanced AI Analysis
 *
 * Displays implicit frame and worldview detection results
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  analyzeImplicitFrames,
  getFrameResults,
  getCategoryInfo,
  getFrameInfo,
  getStrengthLevel
} from '../services/frameApi';

export default function FrameAnalysis() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFrameType, setSelectedFrameType] = useState(null);

  useEffect(() => {
    loadResults();
  }, [conversationId]);

  const loadResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getFrameResults(conversationId);
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
      const data = await analyzeImplicitFrames(conversationId, forceReanalysis);
      setResults(data);
      alert(`Analysis complete! Found ${data.frame_count} frames in ${data.nodes_with_frames} nodes.`);
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const getFilteredNodes = () => {
    if (!results || !results.nodes) return [];

    return results.nodes.filter(node => {
      if (node.frame_count === 0) return false;

      if (selectedCategory) {
        const hasCategory = node.frames.some(f => f.category === selectedCategory);
        if (!hasCategory) return false;
      }

      if (selectedFrameType) {
        const hasFrame = node.frames.some(f => f.frame_type === selectedFrameType);
        if (!hasFrame) return false;
      }

      return true;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading frame analysis...</p>
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
            <h1 className="text-3xl font-bold text-gray-800">Implicit Frame Analysis</h1>
            <p className="text-gray-600 mt-1">
              Detection of underlying worldviews, assumptions, and interpretive frameworks
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
          {/* Summary Cards */}
          <div className="max-w-7xl mx-auto mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-sm text-gray-600 mb-1">Total Nodes</p>
                <p className="text-3xl font-bold text-gray-800">{results.total_nodes}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-sm text-gray-600 mb-1">Nodes with Frames</p>
                <p className="text-3xl font-bold text-purple-600">{results.nodes_with_frames}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {((results.nodes_with_frames / results.total_nodes) * 100).toFixed(1)}% of nodes
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-sm text-gray-600 mb-1">Total Frames</p>
                <p className="text-3xl font-bold text-blue-600">{results.frame_count}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-sm text-gray-600 mb-1">Avg per Node</p>
                <p className="text-3xl font-bold text-green-600">
                  {results.nodes_with_frames > 0
                    ? (results.frame_count / results.nodes_with_frames).toFixed(1)
                    : '0'}
                </p>
              </div>
            </div>
          </div>

          {/* Category Distribution */}
          <div className="max-w-7xl mx-auto mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Distribution by Category</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(results.by_category || {}).map(([category, count]) => {
                const info = getCategoryInfo(category);
                const percentage = results.frame_count > 0
                  ? ((count / results.frame_count) * 100).toFixed(1)
                  : 0;
                const isSelected = selectedCategory === category;

                return (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(isSelected ? null : category)}
                    className={`${info.bgColor} ${info.borderColor} border-2 rounded-lg p-4 text-left transition hover:shadow-lg ${
                      isSelected ? 'ring-4 ring-blue-300' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-lg font-bold ${info.color}`}>
                        {info.name}
                      </span>
                      <span className="text-2xl font-bold text-gray-800">{count}</span>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">
                      {info.description}
                    </p>
                    <div className="bg-white rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full ${info.bgColor.replace('100', '500')}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{percentage}% of frames</p>
                  </button>
                );
              })}
            </div>

            {selectedCategory && (
              <div className="mt-3 text-center">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Clear category filter
                </button>
              </div>
            )}
          </div>

          {/* Top Frames */}
          <div className="max-w-7xl mx-auto mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Most Common Frames</h2>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex flex-wrap gap-2">
                {Object.entries(results.by_frame || {})
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 10)
                  .map(([frameType, count]) => {
                    const isSelected = selectedFrameType === frameType;
                    return (
                      <button
                        key={frameType}
                        onClick={() => setSelectedFrameType(isSelected ? null : frameType)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {getFrameInfo(frameType).split(':')[0]} ({count})
                      </button>
                    );
                  })}
              </div>
              {selectedFrameType && (
                <div className="mt-3">
                  <button
                    onClick={() => setSelectedFrameType(null)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Clear frame filter
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Nodes with Frames */}
          <div className="max-w-7xl mx-auto">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Detected Frames
              {(selectedCategory || selectedFrameType) && ` (${filteredNodes.length} nodes)`}
            </h2>

            {filteredNodes.length > 0 ? (
              <div className="space-y-4">
                {filteredNodes.map((node) => {
                  // Filter node's frames if category/type selected
                  let displayFrames = node.frames;
                  if (selectedCategory) {
                    displayFrames = displayFrames.filter(f => f.category === selectedCategory);
                  }
                  if (selectedFrameType) {
                    displayFrames = displayFrames.filter(f => f.frame_type === selectedFrameType);
                  }

                  if (displayFrames.length === 0) return null;

                  return (
                    <div
                      key={node.node_id}
                      className="bg-white rounded-lg shadow hover:shadow-lg transition"
                    >
                      <div className="p-6">
                        {/* Node Header */}
                        <div className="mb-4">
                          <h3 className="text-lg font-semibold text-gray-800 mb-2">
                            {node.node_name}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {displayFrames.length} {displayFrames.length === 1 ? 'frame' : 'frames'} detected
                          </p>
                        </div>

                        {/* Frames */}
                        <div className="space-y-4">
                          {displayFrames.map((frame, i) => {
                            const categoryInfo = getCategoryInfo(frame.category);
                            const strengthInfo = getStrengthLevel(frame.strength);

                            return (
                              <div
                                key={i}
                                className={`${categoryInfo.bgColor} ${categoryInfo.borderColor} border rounded-lg p-4`}
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex-1">
                                    <p className={`font-bold ${categoryInfo.color} mb-1`}>
                                      {getFrameInfo(frame.frame_type)}
                                    </p>
                                    <div className="flex items-center gap-2 text-xs">
                                      <span className={`font-medium ${strengthInfo.color}`}>
                                        Strength: {strengthInfo.level}
                                      </span>
                                      <span className="text-gray-500">
                                        Confidence: {(frame.confidence * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                <p className="text-sm text-gray-700 mb-3">
                                  {frame.description}
                                </p>

                                {/* Evidence */}
                                {frame.evidence && frame.evidence.length > 0 && (
                                  <div className="mb-3">
                                    <p className="text-xs font-medium text-gray-600 mb-1">Evidence:</p>
                                    <ul className="space-y-1">
                                      {frame.evidence.map((evidence, j) => (
                                        <li
                                          key={j}
                                          className="text-sm text-gray-600 bg-white bg-opacity-50 rounded p-2"
                                        >
                                          "{evidence}"
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* Assumptions (unique to frames) */}
                                {frame.assumptions && frame.assumptions.length > 0 && (
                                  <div className="mb-3">
                                    <p className="text-xs font-medium text-gray-600 mb-1">Underlying Assumptions:</p>
                                    <ul className="space-y-1">
                                      {frame.assumptions.map((assumption, j) => (
                                        <li
                                          key={j}
                                          className="text-sm text-gray-700 bg-white bg-opacity-50 rounded p-2 flex items-start"
                                        >
                                          <span className="mr-2">•</span>
                                          <span>{assumption}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* Implications (unique to frames) */}
                                {frame.implications && (
                                  <div>
                                    <p className="text-xs font-medium text-gray-600 mb-1">Worldview Implications:</p>
                                    <p className="text-sm text-gray-700 bg-white bg-opacity-50 rounded p-2 italic">
                                      {frame.implications}
                                    </p>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-gray-500 text-lg">
                  {selectedCategory || selectedFrameType
                    ? 'No nodes match the selected filters'
                    : 'No frames detected in any nodes'}
                </p>
                {(selectedCategory || selectedFrameType) && (
                  <button
                    onClick={() => {
                      setSelectedCategory(null);
                      setSelectedFrameType(null);
                    }}
                    className="mt-4 text-blue-600 hover:text-blue-800"
                  >
                    Clear all filters
                  </button>
                )}
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
              Click "Run Analysis" to detect implicit frames and underlying worldviews in conversation nodes.
            </p>
            <p className="text-sm text-gray-500 mb-8">
              This will analyze each node for 36+ types of frames across economic, moral, political,
              scientific, cultural, and temporal dimensions.
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
