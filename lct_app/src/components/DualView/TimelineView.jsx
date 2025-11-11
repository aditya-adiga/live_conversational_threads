/**
 * TimelineView Component
 *
 * Displays conversation nodes in chronological/temporal order (left-to-right).
 * Shows temporal edges (sequential flow of conversation).
 * Occupies bottom 15% of the dual-view canvas.
 */

import { useMemo, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import ReactFlow, { Controls, Background, MiniMap, useReactFlow } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

export default function TimelineView({
  nodes,
  edges,
  selectedNode,
  onNodeSelect,
  viewport,
  onViewportChange,
  zoomLevel,
}) {
  const reactFlowInstance = useReactFlow();

  // Filter to show only temporal edges
  const temporalEdges = useMemo(() => {
    return edges.filter(edge => edge.data?.relationshipType === 'temporal');
  }, [edges]);

  // Apply dagre layout for left-to-right temporal flow
  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Left-to-right layout for timeline
    dagreGraph.setGraph({
      rankdir: 'LR', // Left to right
      nodesep: 100,
      ranksep: 150,
      marginx: 50,
      marginy: 50,
    });

    // Add nodes to dagre
    nodes.forEach((node) => {
      dagreGraph.setNode(node.id, {
        width: 150,
        height: 60,
      });
    });

    // Add temporal edges to dagre
    temporalEdges.forEach((edge) => {
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
      layoutedEdges: temporalEdges,
    };
  }, [nodes, temporalEdges]);

  // Style nodes based on selection and zoom level
  const styledNodes = useMemo(() => {
    return layoutedNodes.map((node) => {
      const isSelected = node.id === selectedNode;
      const hasCurrentZoom = node.data.zoomLevels?.includes(zoomLevel);

      return {
        ...node,
        style: {
          ...node.style,
          background: isSelected ? '#ffcc00' : hasCurrentZoom ? 'white' : '#f3f4f6',
          border: isSelected ? '3px solid #ff8800' : hasCurrentZoom ? '2px solid #3b82f6' : '1px solid #d1d5db',
          boxShadow: isSelected ? '0px 0px 15px rgba(255, 136, 0, 0.8)' : hasCurrentZoom ? '0px 2px 8px rgba(0, 0, 0, 0.1)' : 'none',
          opacity: hasCurrentZoom ? 1 : 0.5,
          transition: 'all 0.3s ease-in-out',
          fontSize: '12px',
          padding: '8px',
        },
        data: {
          ...node.data,
          label: node.data.label.length > 25 ? `${node.data.label.substring(0, 25)}...` : node.data.label,
        },
      };
    });
  }, [layoutedNodes, selectedNode, zoomLevel]);

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
      onViewportChange(newViewport, 'timeline');
    },
    [onViewportChange]
  );

  // Sync viewport from parent
  useEffect(() => {
    if (reactFlowInstance && viewport) {
      reactFlowInstance.setViewport(viewport, { duration: 200 });
    }
  }, [viewport, reactFlowInstance]);

  return (
    <div className="h-full w-full bg-gray-50 border-t-2 border-gray-300">
      {/* Header */}
      <div className="absolute top-2 left-4 z-10 bg-white/90 px-3 py-1 rounded-lg shadow-sm border border-gray-300">
        <span className="text-xs font-semibold text-gray-700">
          TIMELINE VIEW • {styledNodes.length} nodes
        </span>
      </div>

      {/* ReactFlow */}
      <ReactFlow
        nodes={styledNodes}
        edges={layoutedEdges}
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
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Controls
          showZoom={false}
          showFitView={true}
          showInteractive={false}
          className="bg-white/90 border border-gray-300"
        />
        <Background color="#e5e7eb" gap={16} />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === selectedNode) return '#ff8800';
            return node.data.zoomLevels?.includes(zoomLevel) ? '#3b82f6' : '#d1d5db';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          style={{
            background: 'white',
            border: '1px solid #d1d5db',
          }}
        />
      </ReactFlow>
    </div>
  );
}

TimelineView.propTypes = {
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
