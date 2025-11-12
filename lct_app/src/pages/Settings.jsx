/**
 * Settings Page
 * Week 9: Prompts Configuration System
 *
 * Allows users to view, edit, and manage LLM prompts
 * Features:
 * - List all prompts
 * - Edit prompt templates and metadata
 * - View version history
 * - Restore previous versions
 * - Validate before saving
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listPrompts,
  getPrompt,
  updatePrompt,
  getPromptHistory,
  restorePromptVersion,
  validatePrompt,
  reloadPrompts
} from '../services/promptsApi';

export default function Settings() {
  const navigate = useNavigate();

  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [promptConfig, setPromptConfig] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [saveComment, setSaveComment] = useState('');

  useEffect(() => {
    loadPrompts();
  }, []);

  useEffect(() => {
    if (selectedPrompt) {
      loadPromptDetails();
    }
  }, [selectedPrompt]);

  const loadPrompts = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await listPrompts();
      setPrompts(data.prompts);

      if (data.prompts.length > 0 && !selectedPrompt) {
        setSelectedPrompt(data.prompts[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPromptDetails = async () => {
    if (!selectedPrompt) return;

    try {
      const config = await getPrompt(selectedPrompt);
      setPromptConfig(config);
      setEditedConfig(null);
      setIsEditing(false);
      setValidationErrors([]);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadHistory = async () => {
    if (!selectedPrompt) return;

    try {
      const historyData = await getPromptHistory(selectedPrompt, 20);
      setHistory(historyData.history);
      setShowHistory(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = () => {
    setEditedConfig({ ...promptConfig });
    setIsEditing(true);
    setValidationErrors([]);
  };

  const handleCancel = () => {
    setEditedConfig(null);
    setIsEditing(false);
    setValidationErrors([]);
    setSaveComment('');
  };

  const handleSave = async () => {
    if (!editedConfig) return;

    // Validate first
    try {
      const validation = await validatePrompt(selectedPrompt, editedConfig);

      if (!validation.valid) {
        setValidationErrors(validation.errors);
        return;
      }
    } catch (err) {
      setError(`Validation failed: ${err.message}`);
      return;
    }

    // Save
    setSaving(true);
    setValidationErrors([]);

    try {
      await updatePrompt(selectedPrompt, editedConfig, 'user', saveComment);

      // Reload
      await loadPromptDetails();
      setSaveComment('');
      alert('Prompt saved successfully!');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (versionTimestamp) => {
    if (!confirm(`Restore prompt to version ${versionTimestamp}?`)) return;

    try {
      await restorePromptVersion(selectedPrompt, versionTimestamp, 'user');
      await loadPromptDetails();
      setShowHistory(false);
      alert('Prompt restored successfully!');
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReload = async () => {
    try {
      await reloadPrompts();
      await loadPrompts();
      alert('Prompts reloaded from file!');
    } catch (err) {
      setError(err.message);
    }
  };

  const currentConfig = isEditing ? editedConfig : promptConfig;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
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
            <h1 className="text-3xl font-bold text-gray-800">Settings</h1>
            <p className="text-gray-600 mt-1">Manage LLM Prompts Configuration</p>
          </div>
          <button
            onClick={handleReload}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition"
          >
            Reload from File
          </button>
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

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Prompt List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-bold text-gray-800 mb-3">Prompts ({prompts.length})</h2>
              <div className="space-y-2">
                {prompts.map((promptName) => (
                  <button
                    key={promptName}
                    onClick={() => setSelectedPrompt(promptName)}
                    className={`w-full text-left px-3 py-2 rounded transition ${
                      selectedPrompt === promptName
                        ? 'bg-blue-100 text-blue-800 font-medium'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    {promptName.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Panel - Prompt Editor */}
          <div className="lg:col-span-3">
            {currentConfig ? (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">{selectedPrompt}</h2>
                    <p className="text-gray-600 text-sm mt-1">{currentConfig.description}</p>
                  </div>
                  <div className="flex gap-2">
                    {!isEditing ? (
                      <>
                        <button
                          onClick={() => loadHistory()}
                          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition"
                        >
                          View History
                        </button>
                        <button
                          onClick={handleEdit}
                          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                        >
                          Edit Prompt
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={handleCancel}
                          className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                          disabled={saving}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSave}
                          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                          disabled={saving}
                        >
                          {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Validation Errors */}
                {validationErrors.length > 0 && (
                  <div className="bg-red-50 border border-red-300 rounded-lg p-3 mb-4">
                    <p className="font-medium text-red-800 mb-2">Validation Errors:</p>
                    <ul className="text-sm text-red-700 space-y-1">
                      {validationErrors.map((err, i) => (
                        <li key={i}>• {err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Save Comment (when editing) */}
                {isEditing && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Change Comment (optional)
                    </label>
                    <input
                      type="text"
                      value={saveComment}
                      onChange={(e) => setSaveComment(e.target.value)}
                      placeholder="Describe your changes..."
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                )}

                {/* Metadata */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                    {isEditing ? (
                      <select
                        value={editedConfig.model}
                        onChange={(e) => setEditedConfig({ ...editedConfig, model: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="claude-sonnet-4">Claude Sonnet 4</option>
                      </select>
                    ) : (
                      <p className="text-gray-800 font-medium">{currentConfig.model}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={editedConfig.temperature}
                        onChange={(e) =>
                          setEditedConfig({ ...editedConfig, temperature: parseFloat(e.target.value) })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-800 font-medium">{currentConfig.temperature}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editedConfig.max_tokens}
                        onChange={(e) =>
                          setEditedConfig({ ...editedConfig, max_tokens: parseInt(e.target.value) })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-800 font-medium">{currentConfig.max_tokens}</p>
                    )}
                  </div>
                </div>

                {/* Template */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt Template
                  </label>
                  {isEditing ? (
                    <textarea
                      value={editedConfig.template}
                      onChange={(e) => setEditedConfig({ ...editedConfig, template: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      rows={20}
                    />
                  ) : (
                    <pre className="bg-gray-50 border border-gray-300 rounded p-4 overflow-x-auto text-sm font-mono whitespace-pre-wrap">
                      {currentConfig.template}
                    </pre>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Use $variable or ${{variable}} syntax for variable substitution
                  </p>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedConfig.description}
                      onChange={(e) => setEditedConfig({ ...editedConfig, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-gray-700">{currentConfig.description}</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                Select a prompt to view details
              </div>
            )}
          </div>
        </div>

        {/* History Modal */}
        {showHistory && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-800">
                  Version History: {selectedPrompt}
                </h3>
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                {history.length > 0 ? (
                  <div className="space-y-4">
                    {history.map((version, i) => (
                      <div
                        key={i}
                        className="border border-gray-300 rounded-lg p-4 hover:bg-gray-50"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-medium text-gray-600 bg-gray-200 px-2 py-1 rounded">
                                {version.change_type}
                              </span>
                              <span className="text-xs text-gray-500">{version.timestamp}</span>
                              <span className="text-xs text-gray-500">by {version.user_id}</span>
                            </div>
                            {version.comment && (
                              <p className="text-sm text-gray-700 mb-2">{version.comment}</p>
                            )}
                            <details className="text-sm">
                              <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                                View Configuration
                              </summary>
                              <pre className="bg-gray-50 border border-gray-200 rounded p-2 mt-2 overflow-x-auto text-xs">
                                {JSON.stringify(version.prompt_config, null, 2)}
                              </pre>
                            </details>
                          </div>
                          <button
                            onClick={() => handleRestore(version.timestamp)}
                            className="ml-4 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition"
                          >
                            Restore
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center">No version history available</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
