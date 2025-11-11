/**
 * DualViewCanvas Component
 *
 * Main container for the dual-view architecture.
 * Combines TimelineView (bottom 15%) and ContextualNetworkView (top 85%)
 * with synchronized zoom, pan, and selection state.
 */

import { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import { ReactFlowProvider } from 'reactflow';
import TimelineView from './TimelineView';
import ContextualNetworkView from './ContextualNetworkView';
import useSyncController from '../../hooks/useSyncController';
import {
  fetchGraph,
  transformNodesToReactFlow,
  transformEdgesToReactFlow,
  getZoomLevelName,
} from '../../services/graphApi';
import 'reactflow/dist/style.css';

export default function DualViewCanvas({ conversationId }) {
  // Sync controller for synchronized state
  const syncController = useSyncController(3); // Start at zoom level 3 (TOPIC)

  // Graph data state
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load graph data from backend
  useEffect(() => {
    if (!conversationId) {
      setError('No conversation ID provided');
      setLoading(false);
      return;
    }

    const loadGraphData = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchGraph(conversationId, null, true);
        setGraphData(data);
      } catch (err) {
        console.error('Failed to load graph data:', err);
        setError(err.message || 'Failed to load graph data');
      } finally {
        setLoading(false);
      }
    };

    loadGraphData();
  }, [conversationId]);

  // Transform backend data to ReactFlow format
  const { nodes, edges } = useMemo(() => {
    if (!graphData) {
      return { nodes: [], edges: [] };
    }

    const nodes = transformNodesToReactFlow(
      graphData.nodes,
      syncController.zoomLevel
    );

    const edges = transformEdgesToReactFlow(graphData.edges);

    return { nodes, edges };
  }, [graphData, syncController.zoomLevel]);

  // Filter nodes by current zoom level for visibility
  const visibleNodes = useMemo(() => {
    return nodes.filter(node =>
      node.data.zoomLevels?.includes(syncController.zoomLevel)
    );
  }, [nodes, syncController.zoomLevel]);

  // Handle zoom level change with keyboard
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === '+' || event.key === '=') {
        syncController.zoomIn();
      } else if (event.key === '-' || event.key === '_') {
        syncController.zoomOut();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [syncController]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-500 to-purple-600">
        <div className="bg-white rounded-lg shadow-2xl p-8 flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
          <span className="text-lg font-semibold text-gray-700">Loading graph...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-red-500 to-pink-600">
        <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Graph</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (!graphData || nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-500 to-gray-700">
        <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">No Graph Data</h2>
          <p className="text-gray-600 mb-4">
            No graph has been generated for this conversation yet.
          </p>
          <button
            onClick={() => window.location.href = `/conversations/${conversationId}`}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Go to Conversation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600">
      {/* Top Control Bar */}
      <div className="w-full px-6 py-4 bg-white/10 backdrop-blur-md shadow-lg flex items-center justify-between">
        {/* Left: Conversation Info */}
        <div className="flex flex-col">
          <span className="text-sm text-white/80 font-medium">Conversation</span>
          <span className="text-lg font-bold text-white">{graphData.conversation_id}</span>
        </div>

        {/* Center: Zoom Controls */}
        <div className="flex items-center gap-4 bg-white/20 backdrop-blur-sm rounded-lg px-6 py-3">
          <button
            onClick={syncController.zoomOut}
            disabled={syncController.isZoomLevelMax}
            className="px-4 py-2 bg-white text-blue-600 font-bold rounded-lg shadow hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            −
          </button>

          <div className="flex flex-col items-center min-w-[120px]">
            <span className="text-xs text-white/90 font-semibold">ZOOM LEVEL</span>
            <span className="text-3xl font-bold text-white">{syncController.zoomLevel}</span>
            <span className="text-sm text-white/90">{getZoomLevelName(syncController.zoomLevel)}</span>
          </div>

          <button
            onClick={syncController.zoomIn}
            disabled={syncController.isZoomLevelMin}
            className="px-4 py-2 bg-white text-blue-600 font-bold rounded-lg shadow hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            +
          </button>
        </div>

        {/* Right: Stats */}
        <div className="flex gap-6 text-white">
          <div className="flex flex-col items-center">
            <span className="text-2xl font-bold">{visibleNodes.length}</span>
            <span className="text-xs text-white/80">visible nodes</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-2xl font-bold">{nodes.length}</span>
            <span className="text-xs text-white/80">total nodes</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-2xl font-bold">{edges.length}</span>
            <span className="text-xs text-white/80">edges</span>
          </div>
        </div>
      </div>

      {/* Dual-View Container */}
      <div className="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
        {/* Top 85%: Contextual Network View */}
        <div className="flex-[85] bg-white rounded-lg shadow-2xl overflow-hidden">
          <ReactFlowProvider>
            <ContextualNetworkView
              nodes={nodes}
              edges={edges}
              selectedNode={syncController.selectedNode}
              onNodeSelect={syncController.setSelectedNode}
              viewport={syncController.viewport}
              onViewportChange={syncController.setViewport}
              zoomLevel={syncController.zoomLevel}
            />
          </ReactFlowProvider>
        </div>

        {/* Bottom 15%: Timeline View */}
        <div className="flex-[15] bg-gray-50 rounded-lg shadow-2xl overflow-hidden border-2 border-gray-300">
          <ReactFlowProvider>
            <TimelineView
              nodes={nodes}
              edges={edges}
              selectedNode={syncController.selectedNode}
              onNodeSelect={syncController.setSelectedNode}
              viewport={syncController.viewport}
              onViewportChange={syncController.setViewport}
              zoomLevel={syncController.zoomLevel}
            />
          </ReactFlowProvider>
        </div>
      </div>

      {/* Keyboard Shortcuts Hint */}
      <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-md text-white px-4 py-2 rounded-lg text-xs">
        <div className="flex gap-4">
          <span><kbd className="bg-white/20 px-2 py-1 rounded">+</kbd> Zoom In</span>
          <span><kbd className="bg-white/20 px-2 py-1 rounded">−</kbd> Zoom Out</span>
        </div>
      </div>
    </div>
  );
}

DualViewCanvas.propTypes = {
  conversationId: PropTypes.string.isRequired,
};
