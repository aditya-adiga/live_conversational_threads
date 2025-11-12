/**
 * Edit History Page
 * Week 10: Edit History & Training Data Export
 *
 * Displays all edits made to conversation nodes, with:
 * - Visual diff of old vs. new values
 * - Filtering by target type
 * - Export to training data formats
 * - Feedback annotations
 * - Statistics summary
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getConversationEdits,
  getEditStatistics,
  downloadTrainingData,
  addEditFeedback
} from '../services/editHistoryApi';

export default function EditHistory() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [edits, setEdits] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [targetTypeFilter, setTargetTypeFilter] = useState(null);
  const [unexportedOnly, setUnexportedOnly] = useState(false);

  // Feedback
  const [feedbackEditId, setFeedbackEditId] = useState(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Exporting
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadEditsAndStats();
  }, [conversationId, targetTypeFilter, unexportedOnly]);

  const loadEditsAndStats = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load edits with filters
      const editsData = await getConversationEdits(conversationId, {
        targetType: targetTypeFilter,
        unexportedOnly
      });

      // Load statistics
      const statsData = await getEditStatistics(conversationId);

      setEdits(editsData.edits);
      setStatistics(statsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    setError(null);

    try {
      await downloadTrainingData(conversationId, format, unexportedOnly);
    } catch (err) {
      setError(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleAddFeedback = async (editId) => {
    if (!feedbackText.trim()) {
      alert('Please enter feedback text');
      return;
    }

    setSubmittingFeedback(true);
    setError(null);

    try {
      await addEditFeedback(editId, feedbackText);
      setFeedbackEditId(null);
      setFeedbackText('');
      await loadEditsAndStats();
      alert('Feedback added successfully!');
    } catch (err) {
      setError(`Failed to add feedback: ${err.message}`);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading edit history...</p>
        </div>
      </div>
    );
  }

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
            <h1 className="text-3xl font-bold text-gray-800">Edit History</h1>
            <p className="text-gray-600 mt-1">
              Track and export all edits made to conversation nodes
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => handleExport('jsonl')}
              disabled={exporting}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition disabled:bg-gray-400"
            >
              {exporting ? 'Exporting...' : 'Export JSONL'}
            </button>
            <button
              onClick={() => handleExport('csv')}
              disabled={exporting}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {exporting ? 'Exporting...' : 'Export CSV'}
            </button>
            <button
              onClick={() => handleExport('markdown')}
              disabled={exporting}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition disabled:bg-gray-400"
            >
              {exporting ? 'Exporting...' : 'Export Markdown'}
            </button>
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

      {/* Statistics Cards */}
      {statistics && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Total Edits</p>
              <p className="text-3xl font-bold text-gray-800">{statistics.total_edits}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Node Edits</p>
              <p className="text-3xl font-bold text-blue-600">{statistics.by_target_type?.node || 0}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Unexported</p>
              <p className="text-3xl font-bold text-orange-600">{statistics.unexported_count}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">With Feedback</p>
              <p className="text-3xl font-bold text-green-600">{statistics.feedback_count || 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Type
              </label>
              <select
                value={targetTypeFilter || ''}
                onChange={(e) => setTargetTypeFilter(e.target.value || null)}
                className="px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="node">Node</option>
                <option value="relationship">Relationship</option>
                <option value="conversation">Conversation</option>
              </select>
            </div>

            <div className="flex items-center mt-6">
              <input
                type="checkbox"
                id="unexported"
                checked={unexportedOnly}
                onChange={(e) => setUnexportedOnly(e.target.checked)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="unexported" className="text-sm font-medium text-gray-700">
                Show only unexported edits
              </label>
            </div>

            <div className="ml-auto">
              <p className="text-sm text-gray-600">
                Showing {edits.length} {edits.length === 1 ? 'edit' : 'edits'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Edits List */}
      <div className="max-w-7xl mx-auto">
        {edits.length > 0 ? (
          <div className="space-y-4">
            {edits.map((edit) => (
              <div
                key={edit.id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition"
              >
                <div className="p-6">
                  {/* Edit Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-medium text-white bg-blue-600 px-2 py-1 rounded">
                          {edit.target_type}
                        </span>
                        <span className="text-xs font-medium text-white bg-purple-600 px-2 py-1 rounded">
                          {edit.edit_type}
                        </span>
                        {!edit.exported && (
                          <span className="text-xs font-medium text-white bg-orange-600 px-2 py-1 rounded">
                            unexported
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(edit.timestamp)}
                        </span>
                      </div>

                      <p className="text-sm text-gray-600">
                        Field: <span className="font-medium text-gray-800">{edit.field_name}</span>
                      </p>

                      {edit.user_comment && (
                        <p className="text-sm text-gray-700 italic mt-1">
                          "{edit.user_comment}"
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Diff Visualization */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <DiffVisualization
                      fieldName={edit.field_name}
                      oldValue={edit.old_value}
                      newValue={edit.new_value}
                    />
                  </div>

                  {/* Feedback Section */}
                  <div className="border-t border-gray-200 pt-4">
                    {edit.feedback && edit.feedback.length > 0 ? (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 mb-2">Feedback:</p>
                        {edit.feedback.map((fb, i) => (
                          <div key={i} className="bg-green-50 rounded p-2 mb-2">
                            <p className="text-sm text-gray-800">{fb.text}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {formatTimestamp(fb.timestamp)}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : null}

                    {feedbackEditId === edit.id ? (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={feedbackText}
                          onChange={(e) => setFeedbackText(e.target.value)}
                          placeholder="Add feedback about this edit..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') handleAddFeedback(edit.id);
                          }}
                        />
                        <button
                          onClick={() => handleAddFeedback(edit.id)}
                          disabled={submittingFeedback}
                          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition disabled:bg-gray-400"
                        >
                          Submit
                        </button>
                        <button
                          onClick={() => {
                            setFeedbackEditId(null);
                            setFeedbackText('');
                          }}
                          className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setFeedbackEditId(edit.id)}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        + Add Feedback
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500 text-lg">No edits found</p>
            <p className="text-gray-400 text-sm mt-2">
              {unexportedOnly
                ? 'All edits have been exported'
                : 'Start editing nodes to see edit history here'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Diff Visualization Component
 * Shows old vs new values with visual highlighting
 */
function DiffVisualization({ fieldName, oldValue, newValue }) {
  // Handle different value types
  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">null</span>;
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const oldFormatted = formatValue(oldValue);
  const newFormatted = formatValue(newValue);

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Old Value */}
      <div>
        <p className="text-xs font-medium text-gray-600 mb-2 uppercase">Before</p>
        <div className="bg-red-50 border border-red-200 rounded p-3">
          <pre className="text-sm text-red-900 whitespace-pre-wrap font-mono">
            {oldFormatted}
          </pre>
        </div>
      </div>

      {/* New Value */}
      <div>
        <p className="text-xs font-medium text-gray-600 mb-2 uppercase">After</p>
        <div className="bg-green-50 border border-green-200 rounded p-3">
          <pre className="text-sm text-green-900 whitespace-pre-wrap font-mono">
            {newFormatted}
          </pre>
        </div>
      </div>
    </div>
  );
}
