/**
 * Node Transition Utilities (Week 6)
 *
 * Utilities for smooth node opacity transitions during zoom level changes.
 */

/**
 * Get transition CSS class based on zoom transition state
 * @param {boolean} isTransitioning - Whether currently transitioning
 * @param {string} transitionDirection - 'in', 'out', or 'none'
 * @param {boolean} isVisible - Whether node is visible at current zoom level
 * @param {boolean} wasVisible - Whether node was visible at previous zoom level
 * @returns {string} CSS transition class
 */
export function getNodeTransitionClass(isTransitioning, transitionDirection, isVisible, wasVisible) {
  if (!isTransitioning) {
    return 'transition-all duration-300 ease-in-out';
  }

  // Node is appearing
  if (isVisible && !wasVisible) {
    return 'transition-all duration-500 ease-out animate-fadeIn';
  }

  // Node is disappearing
  if (!isVisible && wasVisible) {
    return 'transition-all duration-500 ease-in animate-fadeOut';
  }

  // Node remains visible
  return 'transition-all duration-300 ease-in-out';
}

/**
 * Get node opacity based on visibility and transition state
 * @param {boolean} isVisible - Whether node is visible at current zoom level
 * @param {boolean} isTransitioning - Whether currently transitioning
 * @param {number} currentLevel - Current zoom level
 * @param {number} previousLevel - Previous zoom level
 * @param {Array} nodeLevels - Array of zoom levels node is visible at
 * @returns {number} Opacity value (0-1)
 */
export function getNodeOpacity(isVisible, isTransitioning, currentLevel, previousLevel, nodeLevels) {
  if (!isTransitioning) {
    return isVisible ? 1 : 0.4;
  }

  // During transition, gradually fade in/out
  const wasVisible = nodeLevels.includes(previousLevel);

  if (isVisible && !wasVisible) {
    // Fading in
    return 0.7; // Mid-transition opacity
  }

  if (!isVisible && wasVisible) {
    // Fading out
    return 0.6; // Mid-transition opacity
  }

  return isVisible ? 1 : 0.4;
}

/**
 * Get node scale based on visibility and transition state
 * @param {boolean} isVisible - Whether node is visible at current zoom level
 * @param {boolean} isSelected - Whether node is currently selected
 * @param {boolean} isTransitioning - Whether currently transitioning
 * @returns {number} Scale value
 */
export function getNodeScale(isVisible, isSelected, isTransitioning) {
  if (isSelected) {
    return 1.1; // Selected nodes always scaled up
  }

  if (!isVisible) {
    return isTransitioning ? 0.95 : 0.9; // Slightly shrink hidden nodes
  }

  return 1.0;
}

/**
 * Get node border width based on visibility
 * @param {boolean} isVisible - Whether node is visible at current zoom level
 * @param {boolean} isSelected - Whether node is currently selected
 * @returns {string} Border width
 */
export function getNodeBorderWidth(isVisible, isSelected) {
  if (isSelected) {
    return '3px';
  }

  if (isVisible) {
    return '2px';
  }

  return '1px';
}

/**
 * Apply smooth node transitions to ReactFlow node style
 * @param {Object} node - ReactFlow node object
 * @param {Object} transitionState - Transition state { isTransitioning, transitionDirection, currentLevel, previousLevel }
 * @param {boolean} isSelected - Whether node is selected
 * @returns {Object} Updated node with transition styles
 */
export function applyNodeTransitions(node, transitionState, isSelected) {
  const { isTransitioning, transitionDirection, currentLevel, previousLevel } = transitionState;
  const nodeLevels = node.data.zoomLevels || [];

  const isVisible = nodeLevels.includes(currentLevel);
  const wasVisible = nodeLevels.includes(previousLevel);

  const opacity = getNodeOpacity(isVisible, isTransitioning, currentLevel, previousLevel, nodeLevels);
  const scale = getNodeScale(isVisible, isSelected, isTransitioning);
  const borderWidth = getNodeBorderWidth(isVisible, isSelected);
  const transitionClass = getNodeTransitionClass(isTransitioning, transitionDirection, isVisible, wasVisible);

  return {
    ...node,
    style: {
      ...node.style,
      opacity,
      transform: `scale(${scale})`,
      borderWidth,
      transition: 'all 0.3s ease-in-out',
    },
    className: transitionClass,
  };
}

/**
 * CSS keyframes for fade animations (add to your global CSS)
 */
export const TRANSITION_KEYFRAMES = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes fadeOut {
    from {
      opacity: 1;
      transform: scale(1);
    }
    to {
      opacity: 0.4;
      transform: scale(0.9);
    }
  }

  .animate-fadeIn {
    animation: fadeIn 0.5s ease-out forwards;
  }

  .animate-fadeOut {
    animation: fadeOut 0.5s ease-in forwards;
  }
`;
