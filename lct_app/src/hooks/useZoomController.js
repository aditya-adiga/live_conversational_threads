/**
 * Enhanced Zoom Controller Hook (Week 6)
 *
 * Extends Week 5's useSyncController with:
 * - Smooth transitions between zoom levels with animations
 * - Zoom history for back/forward navigation
 * - Zoom-dependent features and context loading
 * - Quantized zoom enforcement (prevents intermediate states)
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook for advanced zoom management with transitions and history
 * @param {number} initialZoomLevel - Initial zoom level (1-5)
 * @param {Object} options - Configuration options
 * @returns {Object} Enhanced zoom controller state and methods
 */
export default function useZoomController(initialZoomLevel = 3, options = {}) {
  const {
    transitionDuration = 300,     // Animation duration in ms
    enableHistory = true,           // Enable zoom history
    maxHistorySize = 20,            // Maximum history entries
    onZoomChange = null,            // Callback when zoom changes
  } = options;

  // Current zoom level (1-5: SENTENCE → TURN → TOPIC → THEME → ARC)
  const [zoomLevel, setZoomLevel] = useState(initialZoomLevel);

  // Previous zoom level (for transition animations)
  const [previousZoomLevel, setPreviousZoomLevel] = useState(initialZoomLevel);

  // Transition state
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Zoom history for back/forward navigation
  const [zoomHistory, setZoomHistory] = useState([initialZoomLevel]);
  const [historyIndex, setHistoryIndex] = useState(0);

  // ReactFlow viewport state (x, y, zoom)
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });

  // Selected node (shared between both views)
  const [selectedNode, setSelectedNode] = useState(null);

  // Track which view is currently being interacted with
  const activeViewRef = useRef(null);

  // Sync lock to prevent infinite update loops
  const syncLockRef = useRef(false);

  // Transition timer ref
  const transitionTimerRef = useRef(null);

  /**
   * Execute zoom level change with animation
   * @param {number} newLevel - New zoom level
   * @param {boolean} addToHistory - Whether to add to history
   */
  const handleZoomLevelChange = useCallback((newLevel, addToHistory = true) => {
    if (newLevel < 1 || newLevel > 5) {
      console.warn(`Invalid zoom level: ${newLevel}. Must be 1-5.`);
      return;
    }

    if (newLevel === zoomLevel) {
      return; // No change
    }

    // Clear existing transition timer
    if (transitionTimerRef.current) {
      clearTimeout(transitionTimerRef.current);
    }

    // Set transition state
    setIsTransitioning(true);
    setPreviousZoomLevel(zoomLevel);
    setZoomLevel(newLevel);

    // Add to history
    if (enableHistory && addToHistory) {
      setZoomHistory(prev => {
        const newHistory = prev.slice(0, historyIndex + 1);
        newHistory.push(newLevel);

        // Limit history size
        if (newHistory.length > maxHistorySize) {
          newHistory.shift();
        }

        return newHistory;
      });
      setHistoryIndex(prev => Math.min(prev + 1, maxHistorySize - 1));
    }

    // Call onChange callback
    if (onZoomChange) {
      onZoomChange({
        from: zoomLevel,
        to: newLevel,
        direction: newLevel < zoomLevel ? 'in' : 'out',
      });
    }

    // End transition after duration
    transitionTimerRef.current = setTimeout(() => {
      setIsTransitioning(false);
      setPreviousZoomLevel(newLevel);
    }, transitionDuration);
  }, [zoomLevel, enableHistory, historyIndex, maxHistorySize, onZoomChange, transitionDuration]);

  /**
   * Zoom in (increase granularity: 5 → 4 → 3 → 2 → 1)
   */
  const zoomIn = useCallback(() => {
    handleZoomLevelChange(Math.max(1, zoomLevel - 1));
  }, [zoomLevel, handleZoomLevelChange]);

  /**
   * Zoom out (decrease granularity: 1 → 2 → 3 → 4 → 5)
   */
  const zoomOut = useCallback(() => {
    handleZoomLevelChange(Math.min(5, zoomLevel + 1));
  }, [zoomLevel, handleZoomLevelChange]);

  /**
   * Jump to specific zoom level
   * @param {number} level - Target zoom level (1-5)
   */
  const jumpToZoomLevel = useCallback((level) => {
    handleZoomLevelChange(level);
  }, [handleZoomLevelChange]);

  /**
   * Navigate back in zoom history
   */
  const zoomHistoryBack = useCallback(() => {
    if (!enableHistory || historyIndex <= 0) {
      return;
    }

    const newIndex = historyIndex - 1;
    const previousLevel = zoomHistory[newIndex];

    setHistoryIndex(newIndex);
    handleZoomLevelChange(previousLevel, false); // Don't add to history
  }, [enableHistory, historyIndex, zoomHistory, handleZoomLevelChange]);

  /**
   * Navigate forward in zoom history
   */
  const zoomHistoryForward = useCallback(() => {
    if (!enableHistory || historyIndex >= zoomHistory.length - 1) {
      return;
    }

    const newIndex = historyIndex + 1;
    const nextLevel = zoomHistory[newIndex];

    setHistoryIndex(newIndex);
    handleZoomLevelChange(nextLevel, false); // Don't add to history
  }, [enableHistory, historyIndex, zoomHistory, handleZoomLevelChange]);

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
   * @param {string} viewId - View identifier
   * @returns {Object} Viewport state
   */
  const getViewportForView = useCallback((viewId) => {
    return viewport;
  }, [viewport]);

  /**
   * Get zoom level name
   * @param {number} level - Zoom level (1-5)
   * @returns {string} Level name
   */
  const getZoomLevelName = useCallback((level) => {
    const names = {
      1: 'SENTENCE',
      2: 'TURN',
      3: 'TOPIC',
      4: 'THEME',
      5: 'ARC',
    };
    return names[level] || 'UNKNOWN';
  }, []);

  /**
   * Get zoom level description
   * @param {number} level - Zoom level (1-5)
   * @returns {string} Level description
   */
  const getZoomLevelDescription = useCallback((level) => {
    const descriptions = {
      1: 'Individual sentences and short exchanges',
      2: 'Speaker turns and complete thoughts',
      3: 'Distinct topics and sub-discussions',
      4: 'Major themes and discussion areas',
      5: 'Overall narrative arcs and meeting segments',
    };
    return descriptions[level] || '';
  }, []);

  /**
   * Get transition direction
   * @returns {string} 'in', 'out', or 'none'
   */
  const getTransitionDirection = useCallback(() => {
    if (!isTransitioning) return 'none';
    return zoomLevel < previousZoomLevel ? 'in' : 'out';
  }, [isTransitioning, zoomLevel, previousZoomLevel]);

  // Cleanup transition timer on unmount
  useEffect(() => {
    return () => {
      if (transitionTimerRef.current) {
        clearTimeout(transitionTimerRef.current);
      }
    };
  }, []);

  return {
    // State
    zoomLevel,
    previousZoomLevel,
    isTransitioning,
    transitionDirection: getTransitionDirection(),
    viewport,
    selectedNode,
    activeView: activeViewRef.current,

    // Zoom Methods
    setZoomLevel: handleZoomLevelChange,
    zoomIn,
    zoomOut,
    jumpToZoomLevel,

    // History Methods
    zoomHistory: enableHistory ? zoomHistory : [],
    historyIndex: enableHistory ? historyIndex : 0,
    canGoBack: enableHistory && historyIndex > 0,
    canGoForward: enableHistory && historyIndex < zoomHistory.length - 1,
    zoomHistoryBack,
    zoomHistoryForward,

    // View Methods
    setViewport: handleViewportChange,
    setSelectedNode: handleNodeSelect,
    resetViewport,
    getViewportForView,

    // Utility Methods
    getZoomLevelName,
    getZoomLevelDescription,

    // Utility State
    isZoomLevelMin: zoomLevel === 1,
    isZoomLevelMax: zoomLevel === 5,
    zoomLevelName: getZoomLevelName(zoomLevel),
    zoomLevelDescription: getZoomLevelDescription(zoomLevel),
  };
}
