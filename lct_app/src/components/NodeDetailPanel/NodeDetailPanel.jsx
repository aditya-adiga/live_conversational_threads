/**
 * NodeDetailPanel Component (Week 7)
 *
 * Split-screen detail view showing selected node with:
 * - Zoom-dependent context loading
 * - Inline editing with explicit edit mode toggle
 * - Immediate save to backend
 */

import { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  getContextNodes,
  getContextConfig,
  getContextDescription,
  canEditNode,
  validateNodeEdits,
  getNodeDiff,
} from '../../utils/contextLoading';

export default function NodeDetailPanel({
  selectedNode,
  allNodes,
  edges,
  zoomLevel,
  onClose,
  onSave,
  utterancesMap = {},
}) {
  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedNode, setEditedNode] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);

  // Load context nodes
  const contextData = useMemo(() => {
    if (!selectedNode) return null;
    return getContextNodes(selectedNode, allNodes, edges, zoomLevel);
  }, [selectedNode, allNodes, edges, zoomLevel]);

  const contextConfig = useMemo(() => {
    return getContextConfig(zoomLevel);
  }, [zoomLevel]);

  // Initialize edited node when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setEditedNode({
        ...selectedNode,
        title: selectedNode.data?.label || '',
        summary: selectedNode.data?.summary || '',
        keywords: selectedNode.data?.keywords || [],
      });
      setIsEditMode(false);
      setSaveError(null);
      setValidationErrors([]);
    }
  }, [selectedNode]);

  if (!selectedNode || !contextData) {
    return null;
  }

  const { previous, current, next, config } = contextData;

  // Handle edit mode toggle
  const handleToggleEditMode = () => {
    if (isEditMode) {
      // Exiting edit mode - reset changes
      setEditedNode({
        ...selectedNode,
        title: selectedNode.data?.label || '',
        summary: selectedNode.data?.summary || '',
        keywords: selectedNode.data?.keywords || [],
      });
      setValidationErrors([]);
    }
    setIsEditMode(!isEditMode);
  };

  // Handle field changes
  const handleFieldChange = (field, value) => {
    setEditedNode(prev => ({
      ...prev,
      [field]: value,
    }));
    setValidationErrors([]);
  };

  // Handle keywords change
  const handleKeywordsChange = (value) => {
    const keywords = value
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);
    handleFieldChange('keywords', keywords);
  };

  // Handle save
  const handleSave = async () => {
    // Validate changes
    const validation = validateNodeEdits(selectedNode, editedNode);
    if (!validation.valid) {
      setValidationErrors(validation.errors);
      return;
    }

    // Get diff
    const diff = getNodeDiff(selectedNode, editedNode);
    if (Object.keys(diff).length === 0) {
      // No changes
      setIsEditMode(false);
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      await onSave(selectedNode.id, editedNode, diff);
      setIsEditMode(false);
      setValidationErrors([]);
    } catch (error) {
      console.error('Failed to save node:', error);
      setSaveError(error.message || 'Failed to save changes');
    } finally {
      setIsSaving(false);
    }
  };

  // Render context node
  const renderContextNode = (node, type) => {
    if (!node) return null;

    return (
      <div className={`p-3 rounded-lg border ${
        type === 'previous' ? 'bg-blue-50 border-blue-200' : 'bg-green-50 border-green-200'
      }`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-gray-500 uppercase">
            {type === 'previous' ? '← Previous' : 'Next →'}
          </span>
        </div>
        <h4 className="font-semibold text-sm text-gray-900 mb-1">
          {node.data?.label}
        </h4>
        {config.showSummary && node.data?.summary && (
          <p className="text-xs text-gray-600 line-clamp-2">
            {node.data.summary}
          </p>
        )}
        {config.showKeywords && node.data?.keywords && node.data.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {node.data.keywords.slice(0, 3).map((keyword, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-0.5 bg-white rounded-full text-gray-600 border border-gray-300"
              >
                {keyword}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white border-l-2 border-gray-300 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-purple-600">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-white animate-pulse" />
          <h2 className="text-lg font-bold text-white">Node Details</h2>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-200 transition text-2xl font-bold"
          title="Close panel"
        >
          ×
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Context Description */}
        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-xs text-purple-800">
            <strong>Zoom Level {zoomLevel}:</strong> {getContextDescription(zoomLevel)}
          </p>
        </div>

        {/* Previous Context */}
        {previous.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Context Before
            </h3>
            {previous.map((node, idx) => (
              <div key={idx}>{renderContextNode(node, 'previous')}</div>
            ))}
          </div>
        )}

        {/* Current Node */}
        <div className="p-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg shadow-md">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-yellow-800 uppercase tracking-wide">
              Selected Node
            </h3>
            <div className="flex gap-2">
              {!isEditMode && canEditNode(selectedNode) && (
                <button
                  onClick={handleToggleEditMode}
                  className="px-3 py-1 text-xs font-semibold bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                  Edit
                </button>
              )}
              {isEditMode && (
                <>
                  <button
                    onClick={handleToggleEditMode}
                    disabled={isSaving}
                    className="px-3 py-1 text-xs font-semibold bg-gray-500 text-white rounded-md hover:bg-gray-600 transition disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-3 py-1 text-xs font-semibold bg-green-600 text-white rounded-md hover:bg-green-700 transition disabled:opacity-50"
                  >
                    {isSaving ? 'Saving...' : 'Save'}
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="mb-3 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
              {validationErrors.map((error, idx) => (
                <div key={idx}>• {error}</div>
              ))}
            </div>
          )}

          {/* Save Error */}
          {saveError && (
            <div className="mb-3 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
              {saveError}
            </div>
          )}

          {/* Title */}
          <div className="mb-3">
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Title
            </label>
            {isEditMode ? (
              <input
                type="text"
                value={editedNode.title}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="Node title..."
              />
            ) : (
              <h4 className="font-bold text-lg text-gray-900">{current.data?.label}</h4>
            )}
          </div>

          {/* Summary */}
          {config.showSummary && (
            <div className="mb-3">
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Summary
              </label>
              {isEditMode ? (
                <textarea
                  value={editedNode.summary}
                  onChange={(e) => handleFieldChange('summary', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="Node summary..."
                />
              ) : (
                <p className="text-sm text-gray-700">
                  {current.data?.summary || 'No summary available'}
                </p>
              )}
            </div>
          )}

          {/* Keywords */}
          {config.showKeywords && (
            <div className="mb-3">
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Keywords
              </label>
              {isEditMode ? (
                <input
                  type="text"
                  value={(editedNode.keywords || []).join(', ')}
                  onChange={(e) => handleKeywordsChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="keyword1, keyword2, keyword3..."
                />
              ) : (
                <div className="flex flex-wrap gap-2">
                  {current.data?.keywords && current.data.keywords.length > 0 ? (
                    current.data.keywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium"
                      >
                        {keyword}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-500">No keywords</span>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Speaker Info */}
          {current.data?.speakerInfo && (
            <div className="mb-3">
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Speaker
              </label>
              <p className="text-sm text-gray-700">
                {current.data.speakerInfo.primary_speaker || 'Unknown'}
              </p>
            </div>
          )}

          {/* Zoom Levels */}
          <div className="mb-3">
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Visible at Zoom Levels
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(level => (
                <span
                  key={level}
                  className={`w-8 h-8 flex items-center justify-center rounded-md text-xs font-bold ${
                    current.data?.zoomLevels?.includes(level)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-400'
                  }`}
                >
                  {level}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Next Context */}
        {next.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Context After
            </h3>
            {next.map((node, idx) => (
              <div key={idx}>{renderContextNode(node, 'next')}</div>
            ))}
          </div>
        )}

        {/* Edit Mode Reminder */}
        {isEditMode && (
          <div className="p-3 bg-orange-50 border border-orange-300 rounded-lg">
            <p className="text-xs text-orange-800">
              <strong>Edit Mode Active:</strong> Make your changes and click Save to update the node.
              Changes will be sent to the backend immediately.
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-600 text-center">
        Press ESC to close • Click outside to deselect node
      </div>
    </div>
  );
}

NodeDetailPanel.propTypes = {
  selectedNode: PropTypes.object,
  allNodes: PropTypes.array.isRequired,
  edges: PropTypes.array.isRequired,
  zoomLevel: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  utterancesMap: PropTypes.object,
};
