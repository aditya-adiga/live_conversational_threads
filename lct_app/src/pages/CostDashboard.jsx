/**
 * Cost Dashboard Page
 * Production Feature: API Cost Tracking and Analytics
 *
 * Displays LLM API usage and costs across all conversations and features
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CostDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [timeRange, setTimeRange] = useState('7d'); // 1d, 7d, 30d, all

  const API_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

  useEffect(() => {
    loadStats();
  }, [timeRange]);

  const loadStats = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/cost-tracking/stats?time_range=${timeRange}`);

      if (!response.ok) {
        throw new Error('Failed to load cost statistics');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading cost statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:text-blue-800 mb-4"
          >
            ← Back
          </button>
          <div className="bg-red-50 border border-red-300 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-700 mb-2">Error Loading Cost Data</h2>
            <p className="text-red-600">{error}</p>
            <p className="text-sm text-red-500 mt-4">
              Make sure cost tracking is enabled in the backend and the endpoint is accessible.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

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
            <h1 className="text-3xl font-bold text-gray-800">Cost Dashboard</h1>
            <p className="text-gray-600 mt-1">
              API usage and cost tracking across all features
            </p>
          </div>

          {/* Time Range Selector */}
          <div className="flex gap-2">
            {['1d', '7d', '30d', 'all'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  timeRange === range
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {range === '1d' && 'Today'}
                {range === '7d' && '7 Days'}
                {range === '30d' && '30 Days'}
                {range === 'all' && 'All Time'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Total Cost</p>
            <p className="text-3xl font-bold text-blue-600">
              {formatCurrency(stats.total_cost || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {formatNumber(stats.total_calls || 0)} API calls
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Avg Cost per Call</p>
            <p className="text-3xl font-bold text-green-600">
              {formatCurrency(stats.avg_cost_per_call || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {formatNumber(stats.avg_tokens_per_call || 0)} tokens avg
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Total Tokens</p>
            <p className="text-3xl font-bold text-purple-600">
              {formatNumber(stats.total_tokens || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Input + Output tokens
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Conversations Analyzed</p>
            <p className="text-3xl font-bold text-orange-600">
              {formatNumber(stats.conversations_analyzed || 0)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {formatCurrency((stats.total_cost || 0) / Math.max(stats.conversations_analyzed || 1, 1))} per conversation
            </p>
          </div>
        </div>
      </div>

      {/* Cost by Feature */}
      <div className="max-w-7xl mx-auto mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Cost by Feature</h2>
        <div className="bg-white rounded-lg shadow p-6">
          {stats.by_feature && Object.keys(stats.by_feature).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(stats.by_feature)
                .sort((a, b) => b[1].cost - a[1].cost)
                .map(([feature, data]) => {
                  const percentage = ((data.cost / stats.total_cost) * 100).toFixed(1);
                  return (
                    <div key={feature} className="border-b border-gray-200 last:border-0 pb-4 last:pb-0">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-medium text-gray-800 capitalize">
                            {feature.replace(/_/g, ' ')}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatNumber(data.calls)} calls • {formatNumber(data.tokens)} tokens
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-gray-800">
                            {formatCurrency(data.cost)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {percentage}% of total
                          </p>
                        </div>
                      </div>
                      <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-blue-600 h-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available for selected time range</p>
          )}
        </div>
      </div>

      {/* Cost by Model */}
      <div className="max-w-7xl mx-auto mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Cost by Model</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats.by_model && Object.keys(stats.by_model).length > 0 ? (
            Object.entries(stats.by_model)
              .sort((a, b) => b[1].cost - a[1].cost)
              .map(([model, data]) => (
                <div key={model} className="bg-white rounded-lg shadow p-6">
                  <p className="text-sm font-medium text-gray-600 mb-2">{model}</p>
                  <p className="text-2xl font-bold text-gray-800 mb-2">
                    {formatCurrency(data.cost)}
                  </p>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>{formatNumber(data.calls)} calls</p>
                    <p>{formatNumber(data.tokens)} tokens</p>
                    <p>Avg: {formatCurrency(data.cost / data.calls)} per call</p>
                  </div>
                </div>
              ))
          ) : (
            <div className="col-span-3 bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">No model data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent API Calls */}
      <div className="max-w-7xl mx-auto">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent API Calls</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {stats.recent_calls && stats.recent_calls.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Feature
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Latency
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stats.recent_calls.map((call, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(call.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                      {call.endpoint?.replace(/_/g, ' ') || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {call.model || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatNumber(call.total_tokens || 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(call.cost_usd || 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {call.latency_ms ? `${call.latency_ms}ms` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-gray-500">
              No recent API calls
            </div>
          )}
        </div>
      </div>

      {/* Footer Note */}
      <div className="max-w-7xl mx-auto mt-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Cost tracking requires the backend API call logging to be enabled.
            If no data appears, check that the <code className="bg-blue-100 px-2 py-1 rounded">api_calls_log</code> table
            exists and cost tracking is configured in your backend.
          </p>
        </div>
      </div>
    </div>
  );
}
