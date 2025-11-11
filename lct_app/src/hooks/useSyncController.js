/**
 * Sync Controller Hook
 *
 * Manages synchronized zoom, pan, and viewport state between Timeline and Contextual views.
 * Ensures both views stay in sync when user interacts with either one.
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Custom hook for synchronizing zoom and pan between two ReactFlow instances
 * @param {number} initialZoomLevel - Initial zoom level (1-5)
 * @returns {Object} Sync controller state and methods
 */
export default function useSyncController(initialZoomLevel = 3) {
  // Current zoom level (1-5: SENTENCE → TURN → TOPIC → THEME → ARC)
  const [zoomLevel, setZoomLevel] = useState(initialZoomLevel);

  // ReactFlow viewport state (x, y, zoom)
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });

  // Selected node (shared between both views)
  const [selectedNode, setSelectedNode] = useState(null);

  // Track which view is currently being interacted with
  const activeViewRef = useRef(null);

  // Sync lock to prevent infinite update loops
  const syncLockRef = useRef(false);

  /**
   * Handle zoom level change (1-5 discrete levels)
   * @param {number} newLevel - New zoom level
   */
  const handleZoomLevelChange = useCallback((newLevel) => {
    if (newLevel < 1 || newLevel > 5) {
      console.warn(`Invalid zoom level: ${newLevel}. Must be 1-5.`);
      return;
    }

    setZoomLevel(newLevel);
  }, []);

  /**
   * Zoom in (increase granularity)
   */
  const zoomIn = useCallback(() => {
    setZoomLevel((prev) => Math.max(1, prev - 1));
  }, []);

  /**
   * Zoom out (decrease granularity)
   */
  const zoomOut = useCallback(() => {
    setZoomLevel((prev) => Math.min(5, prev + 1));
  }, []);

  /**
   * Handle viewport change from either view
   * @param {Object} newViewport - New viewport {x, y, zoom}
   * @param {string} source - Source view identifier ('timeline' or 'contextual')
   */
  const handleViewportChange = useCallback((newViewport, source) => {
    // Prevent sync loop
    if (syncLockRef.current) {
      return;
    }

    syncLockRef.current = true;
    activeViewRef.current = source;
    setViewport(newViewport);

    // Release lock after a short delay
    setTimeout(() => {
      syncLockRef.current = false;
    }, 50);
  }, []);

  /**
   * Handle node selection
   * @param {string|null} nodeId - Selected node ID or null to deselect
   */
  const handleNodeSelect = useCallback((nodeId) => {
    setSelectedNode(nodeId);
  }, []);

  /**
   * Reset viewport to fit view
   */
  const resetViewport = useCallback(() => {
    setViewport({ x: 0, y: 0, zoom: 1 });
  }, []);

  /**
   * Get viewport for a specific view
   * Can be extended to have per-view offsets if needed
   * @param {string} viewId - View identifier
   * @returns {Object} Viewport state
   */
  const getViewportForView = useCallback((viewId) => {
    // Currently returns same viewport for both views
    // Can be customized to have different zoom/pan per view
    return viewport;
  }, [viewport]);

  return {
    // State
    zoomLevel,
    viewport,
    selectedNode,
    activeView: activeViewRef.current,

    // Methods
    setZoomLevel: handleZoomLevelChange,
    zoomIn,
    zoomOut,
    setViewport: handleViewportChange,
    setSelectedNode: handleNodeSelect,
    resetViewport,
    getViewportForView,

    // Utility
    isZoomLevelMin: zoomLevel === 1,
    isZoomLevelMax: zoomLevel === 5,
  };
}
