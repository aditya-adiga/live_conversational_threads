/**
 * ContextualNetworkView Component
 *
 * Displays conversation nodes with contextual/thematic relationships.
 * Shows both temporal and contextual edges with different styling.
 * Occupies top 85% of the dual-view canvas.
 */

import { useMemo, useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import ReactFlow, { Controls, Background, MiniMap, Panel, useReactFlow } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import { getZoomLevelName } from '../../services/graphApi';

export default function ContextualNetworkView({
  nodes,
  edges,
  selectedNode,
  onNodeSelect,
  viewport,
  onViewportChange,
  zoomLevel,
}) {
  const reactFlowInstance = useReactFlow();
  const [showContextualOnly, setShowContextualOnly] = useState(false);

  // Filter edges based on toggle
  const filteredEdges = useMemo(() => {
    if (showContextualOnly) {
      return edges.filter(edge => edge.data?.relationshipType !== 'temporal');
    }
    return edges;
  }, [edges, showContextualOnly]);

  // Apply dagre layout for force-directed graph
  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Top-to-bottom layout for contextual clustering
    dagreGraph.setGraph({
      rankdir: 'TB', // Top to bottom
      nodesep: 80,
      ranksep: 120,
      marginx: 50,
      marginy: 50,
    });

    // Add nodes to dagre
    nodes.forEach((node) => {
      dagreGraph.setNode(node.id, {
        width: 180,
        height: 80,
      });
    });

    // Add edges to dagre (prioritize contextual relationships for layout)
    filteredEdges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    // Calculate layout
    dagre.layout(dagreGraph);

    // Apply calculated positions
    const layoutedNodes = nodes.map((node) => {
      const position = dagreGraph.node(node.id);
      return {
        ...node,
        position: {
          x: position?.x || node.position.x,
          y: position?.y || node.position.y,
        },
      };
    });

    return {
      layoutedNodes,
      layoutedEdges: filteredEdges,
    };
  }, [nodes, filteredEdges]);

  // Style nodes based on selection and zoom level
  const styledNodes = useMemo(() => {
    return layoutedNodes.map((node) => {
      const isSelected = node.id === selectedNode;
      const hasCurrentZoom = node.data.zoomLevels?.includes(zoomLevel);

      return {
        ...node,
        style: {
          ...node.style,
          background: isSelected
            ? 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)'
            : hasCurrentZoom
            ? 'white'
            : '#f9fafb',
          border: isSelected
            ? '3px solid #ff8800'
            : hasCurrentZoom
            ? '2px solid #3b82f6'
            : '1px solid #e5e7eb',
          boxShadow: isSelected
            ? '0px 4px 20px rgba(255, 136, 0, 0.6)'
            : hasCurrentZoom
            ? '0px 2px 12px rgba(59, 130, 246, 0.3)'
            : 'none',
          opacity: hasCurrentZoom ? 1 : 0.4,
          transition: 'all 0.3s ease-in-out',
          fontSize: '13px',
          padding: '12px',
          borderRadius: '10px',
          minWidth: '180px',
        },
        data: {
          ...node.data,
          label: node.data.label,
        },
      };
    });
  }, [layoutedNodes, selectedNode, zoomLevel]);

  // Style edges based on type
  const styledEdges = useMemo(() => {
    return layoutedEdges.map((edge) => {
      const isTemporal = edge.data?.relationshipType === 'temporal';
      const isConnectedToSelection =
        edge.source === selectedNode || edge.target === selectedNode;

      return {
        ...edge,
        animated: !isTemporal && isConnectedToSelection,
        style: {
          ...edge.style,
          stroke: isConnectedToSelection
            ? '#ff8800'
            : isTemporal
            ? '#9ca3af'
            : '#3b82f6',
          strokeWidth: isConnectedToSelection ? 3 : isTemporal ? 2 : 2.5,
          opacity: isConnectedToSelection ? 1 : isTemporal ? 0.4 : 0.7,
          strokeDasharray: isTemporal ? '5, 5' : 'none',
        },
        markerEnd: {
          type: 'arrowclosed',
          width: 12,
          height: 12,
          color: isConnectedToSelection
            ? '#ff8800'
            : isTemporal
            ? '#9ca3af'
            : '#3b82f6',
        },
      };
    });
  }, [layoutedEdges, selectedNode]);

  // Handle node click
  const handleNodeClick = useCallback(
    (event, node) => {
      event.stopPropagation();
      onNodeSelect(node.id === selectedNode ? null : node.id);
    },
    [selectedNode, onNodeSelect]
  );

  // Handle viewport change
  const handleMove = useCallback(
    (event, newViewport) => {
      onViewportChange(newViewport, 'contextual');
    },
    [onViewportChange]
  );

  // Sync viewport from parent
  useEffect(() => {
    if (reactFlowInstance && viewport) {
      reactFlowInstance.setViewport(viewport, { duration: 200 });
    }
  }, [viewport, reactFlowInstance]);

  // Count edge types
  const edgeStats = useMemo(() => {
    const temporal = edges.filter(e => e.data?.relationshipType === 'temporal').length;
    const contextual = edges.filter(e => e.data?.relationshipType !== 'temporal').length;
    return { temporal, contextual };
  }, [edges]);

  return (
    <div className="h-full w-full bg-white relative">
      {/* Header */}
      <Panel position="top-left" className="bg-white/95 px-4 py-2 rounded-lg shadow-lg border border-gray-200 m-2">
        <div className="flex flex-col gap-2">
          <span className="text-sm font-bold text-gray-800">
            CONTEXTUAL NETWORK VIEW
          </span>
          <div className="flex gap-4 text-xs text-gray-600">
            <span>{styledNodes.length} nodes</span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">{edgeStats.temporal} temporal</span>
            <span className="text-blue-600">{edgeStats.contextual} contextual</span>
          </div>
        </div>
      </Panel>

      {/* Zoom Level Indicator */}
      <Panel position="top-right" className="bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-2 rounded-lg shadow-lg m-2">
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-semibold text-white/80">ZOOM LEVEL</span>
          <span className="text-2xl font-bold text-white">{zoomLevel}</span>
          <span className="text-xs text-white/90">{getZoomLevelName(zoomLevel)}</span>
        </div>
      </Panel>

      {/* Edge Filter Toggle */}
      <Panel position="bottom-right" className="bg-white/95 px-3 py-2 rounded-lg shadow-lg border border-gray-200 m-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showContextualOnly}
            onChange={(e) => setShowContextualOnly(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-xs text-gray-700 font-medium">
            Contextual edges only
          </span>
        </label>
      </Panel>

      {/* Selected Node Info */}
      {selectedNode && (
        <Panel position="bottom-left" className="bg-yellow-50 border-2 border-yellow-400 px-4 py-2 rounded-lg shadow-lg m-2 max-w-md">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-yellow-800">SELECTED NODE</span>
            <span className="text-sm font-bold text-gray-800">
              {styledNodes.find(n => n.id === selectedNode)?.data.label}
            </span>
            {styledNodes.find(n => n.id === selectedNode)?.data.summary && (
              <span className="text-xs text-gray-600 mt-1">
                {styledNodes.find(n => n.id === selectedNode)?.data.summary.substring(0, 100)}
                {styledNodes.find(n => n.id === selectedNode)?.data.summary.length > 100 ? '...' : ''}
              </span>
            )}
          </div>
        </Panel>
      )}

      {/* ReactFlow */}
      <ReactFlow
        nodes={styledNodes}
        edges={styledEdges}
        onNodeClick={handleNodeClick}
        onMove={handleMove}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: false,
        }}
        zoomOnScroll={true}
        zoomOnPinch={true}
        panOnDrag={true}
        panOnScroll={false}
        minZoom={0.1}
        maxZoom={2}
        attributionPosition="bottom-center"
        proOptions={{ hideAttribution: true }}
      >
        <Controls
          showZoom={true}
          showFitView={true}
          showInteractive={false}
          className="bg-white/90 border border-gray-300"
        />
        <Background color="#f3f4f6" gap={20} />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === selectedNode) return '#ff8800';
            return node.data.zoomLevels?.includes(zoomLevel) ? '#3b82f6' : '#e5e7eb';
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{
            background: 'white',
            border: '1px solid #d1d5db',
          }}
        />
      </ReactFlow>
    </div>
  );
}

ContextualNetworkView.propTypes = {
  nodes: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      data: PropTypes.shape({
        label: PropTypes.string.isRequired,
        summary: PropTypes.string,
        keywords: PropTypes.array,
        zoomLevels: PropTypes.arrayOf(PropTypes.number),
      }).isRequired,
      position: PropTypes.shape({
        x: PropTypes.number.isRequired,
        y: PropTypes.number.isRequired,
      }).isRequired,
    })
  ).isRequired,
  edges: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      source: PropTypes.string.isRequired,
      target: PropTypes.string.isRequired,
      data: PropTypes.object,
    })
  ).isRequired,
  selectedNode: PropTypes.string,
  onNodeSelect: PropTypes.func.isRequired,
  viewport: PropTypes.shape({
    x: PropTypes.number.isRequired,
    y: PropTypes.number.isRequired,
    zoom: PropTypes.number.isRequired,
  }).isRequired,
  onViewportChange: PropTypes.func.isRequired,
  zoomLevel: PropTypes.number.isRequired,
};
