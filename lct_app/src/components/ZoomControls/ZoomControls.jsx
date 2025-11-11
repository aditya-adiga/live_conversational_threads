/**
 * ZoomControls Component (Week 6)
 *
 * Complete zoom control interface with:
 * - Zoom in/out buttons
 * - History navigation (back/forward)
 * - Level indicator with click-to-jump
 * - Keyboard shortcuts display
 */

import { useEffect } from 'prop-types';
import PropTypes from 'prop-types';
import ZoomLevelIndicator from './ZoomLevelIndicator';

export default function ZoomControls({
  zoomController,
  showHistory = true,
  showLevelIndicator = true,
  showKeyboardHints = false,
  compact = false,
}) {
  const {
    zoomLevel,
    isTransitioning,
    transitionDirection,
    zoomIn,
    zoomOut,
    jumpToZoomLevel,
    canGoBack,
    canGoForward,
    zoomHistoryBack,
    zoomHistoryForward,
    isZoomLevelMin,
    isZoomLevelMax,
    zoomLevelName,
    zoomLevelDescription,
  } = zoomController;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Don't trigger if user is typing in an input
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
      }

      switch (event.key) {
        case '+':
        case '=':
          event.preventDefault();
          zoomIn();
          break;
        case '-':
        case '_':
          event.preventDefault();
          zoomOut();
          break;
        case 'ArrowLeft':
          if (event.altKey && showHistory) {
            event.preventDefault();
            zoomHistoryBack();
          }
          break;
        case 'ArrowRight':
          if (event.altKey && showHistory) {
            event.preventDefault();
            zoomHistoryForward();
          }
          break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            jumpToZoomLevel(parseInt(event.key));
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [zoomIn, zoomOut, jumpToZoomLevel, zoomHistoryBack, zoomHistoryForward, showHistory]);

  if (compact) {
    return (
      <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg border border-gray-200">
        {/* Zoom Out */}
        <button
          onClick={zoomOut}
          disabled={isZoomLevelMax || isTransitioning}
          className="w-8 h-8 flex items-center justify-center bg-white text-gray-700 font-bold rounded-md shadow hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
          title="Zoom Out (−)"
        >
          −
        </button>

        {/* Current Level */}
        <div className="flex flex-col items-center min-w-[60px]">
          <span className="text-xs text-gray-500 font-semibold">LEVEL</span>
          <span className="text-xl font-bold text-gray-900">{zoomLevel}</span>
        </div>

        {/* Zoom In */}
        <button
          onClick={zoomIn}
          disabled={isZoomLevelMin || isTransitioning}
          className="w-8 h-8 flex items-center justify-center bg-white text-gray-700 font-bold rounded-md shadow hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
          title="Zoom In (+)"
        >
          +
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 bg-white/95 backdrop-blur-sm rounded-lg p-4 shadow-lg border border-gray-200">
      {/* Top Section: Zoom Buttons */}
      <div className="flex items-center gap-3">
        {/* Zoom Out Button */}
        <button
          onClick={zoomOut}
          disabled={isZoomLevelMax || isTransitioning}
          className="px-4 py-3 bg-white text-blue-600 font-bold text-xl rounded-lg shadow hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center min-w-[60px]"
          title="Zoom Out (−)"
        >
          −
        </button>

        {/* Current Level Display */}
        <div className="flex flex-col items-center justify-center px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-md min-w-[140px]">
          <span className="text-xs text-white/80 font-semibold">ZOOM LEVEL</span>
          <span className="text-3xl font-bold text-white">{zoomLevel}</span>
          <span className="text-sm text-white/90">{zoomLevelName}</span>
        </div>

        {/* Zoom In Button */}
        <button
          onClick={zoomIn}
          disabled={isZoomLevelMin || isTransitioning}
          className="px-4 py-3 bg-white text-blue-600 font-bold text-xl rounded-lg shadow hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center min-w-[60px]"
          title="Zoom In (+)"
        >
          +
        </button>
      </div>

      {/* Level Indicator */}
      {showLevelIndicator && (
        <div className="flex justify-center">
          <ZoomLevelIndicator
            currentLevel={zoomLevel}
            onLevelChange={jumpToZoomLevel}
            isTransitioning={isTransitioning}
            transitionDirection={transitionDirection}
            showLabels={true}
            showDescription={false}
            orientation="horizontal"
          />
        </div>
      )}

      {/* History Navigation */}
      {showHistory && (
        <div className="flex items-center justify-center gap-2 pt-2 border-t border-gray-200">
          <button
            onClick={zoomHistoryBack}
            disabled={!canGoBack || isTransitioning}
            className="px-3 py-1.5 bg-white text-gray-700 text-sm font-medium rounded-md shadow hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-1"
            title="Zoom History Back (Alt + ←)"
          >
            <span>←</span>
            <span>Back</span>
          </button>

          <span className="text-xs text-gray-500 font-medium">HISTORY</span>

          <button
            onClick={zoomHistoryForward}
            disabled={!canGoForward || isTransitioning}
            className="px-3 py-1.5 bg-white text-gray-700 text-sm font-medium rounded-md shadow hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-1"
            title="Zoom History Forward (Alt + →)"
          >
            <span>Forward</span>
            <span>→</span>
          </button>
        </div>
      )}

      {/* Description */}
      <div className="text-center text-xs text-gray-600 pt-1 border-t border-gray-100">
        {zoomLevelDescription}
      </div>

      {/* Keyboard Shortcuts */}
      {showKeyboardHints && (
        <div className="flex flex-col gap-1 pt-2 border-t border-gray-100 text-xs text-gray-500">
          <div className="flex justify-between">
            <span><kbd className="bg-gray-200 px-1.5 py-0.5 rounded">+</kbd> / <kbd className="bg-gray-200 px-1.5 py-0.5 rounded">−</kbd></span>
            <span>Zoom in/out</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-gray-200 px-1.5 py-0.5 rounded">Ctrl</kbd> + <kbd className="bg-gray-200 px-1.5 py-0.5 rounded">1-5</kbd></span>
            <span>Jump to level</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-gray-200 px-1.5 py-0.5 rounded">Alt</kbd> + <kbd className="bg-gray-200 px-1.5 py-0.5 rounded">←</kbd> / <kbd className="bg-gray-200 px-1.5 py-0.5 rounded">→</kbd></span>
            <span>History navigation</span>
          </div>
        </div>
      )}
    </div>
  );
}

ZoomControls.propTypes = {
  zoomController: PropTypes.shape({
    zoomLevel: PropTypes.number.isRequired,
    isTransitioning: PropTypes.bool.isRequired,
    transitionDirection: PropTypes.string.isRequired,
    zoomIn: PropTypes.func.isRequired,
    zoomOut: PropTypes.func.isRequired,
    jumpToZoomLevel: PropTypes.func.isRequired,
    canGoBack: PropTypes.bool,
    canGoForward: PropTypes.bool,
    zoomHistoryBack: PropTypes.func,
    zoomHistoryForward: PropTypes.func,
    isZoomLevelMin: PropTypes.bool.isRequired,
    isZoomLevelMax: PropTypes.bool.isRequired,
    zoomLevelName: PropTypes.string.isRequired,
    zoomLevelDescription: PropTypes.string.isRequired,
  }).isRequired,
  showHistory: PropTypes.bool,
  showLevelIndicator: PropTypes.bool,
  showKeyboardHints: PropTypes.bool,
  compact: PropTypes.bool,
};
