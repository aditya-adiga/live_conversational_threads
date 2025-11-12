/**
 * Analytics Page
 * Week 8: Speaker Analytics
 *
 * Displays comprehensive speaker statistics including:
 * - Time spoken per speaker
 * - Turn distribution
 * - Speaker roles
 * - Topic dominance
 * - Timeline visualization
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchConversationAnalytics } from '../services/analyticsApi';

export default function Analytics() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);
  const [sortBy, setSortBy] = useState('time'); // 'time', 'turns', 'topics'

  useEffect(() => {
    loadAnalytics();
  }, [conversationId]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchConversationAnalytics(conversationId);
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'facilitator':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'contributor':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'observer':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-purple-100 text-purple-800 border-purple-300';
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'facilitator':
        return '🎯';
      case 'contributor':
        return '💬';
      case 'observer':
        return '👁️';
      default:
        return '👤';
    }
  };

  const getSortedSpeakers = () => {
    if (!analytics?.speakers) return [];

    const speakerArray = Object.values(analytics.speakers);

    switch (sortBy) {
      case 'time':
        return speakerArray.sort((a, b) => b.time_spoken_seconds - a.time_spoken_seconds);
      case 'turns':
        return speakerArray.sort((a, b) => b.turn_count - a.turn_count);
      case 'topics':
        return speakerArray.sort((a, b) => b.topics_dominated.length - a.topics_dominated.length);
      default:
        return speakerArray;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <div className="text-red-600 text-4xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Analytics</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadAnalytics}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mr-2"
          >
            Retry
          </button>
          <button
            onClick={() => navigate(-1)}
            className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const sortedSpeakers = getSortedSpeakers();

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
              ← Back to Conversation
            </button>
            <h1 className="text-3xl font-bold text-gray-800">Speaker Analytics</h1>
            <p className="text-gray-600 mt-1">{analytics.summary.conversation_name}</p>
          </div>
          <button
            onClick={loadAnalytics}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Refresh Analytics
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-500 text-sm font-medium">Total Duration</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">
              {formatTime(analytics.summary.total_duration)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-500 text-sm font-medium">Total Turns</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">
              {analytics.summary.total_turns}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-500 text-sm font-medium">Speakers</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">
              {analytics.summary.total_speakers}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-500 text-sm font-medium">Avg Turn Duration</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">
              {formatTime(
                analytics.summary.total_duration / analytics.summary.total_turns
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Speaker Cards Section */}
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">Speaker Breakdown</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy('time')}
                className={`px-3 py-1 rounded text-sm font-medium transition ${
                  sortBy === 'time'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                By Time
              </button>
              <button
                onClick={() => setSortBy('turns')}
                className={`px-3 py-1 rounded text-sm font-medium transition ${
                  sortBy === 'turns'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                By Turns
              </button>
              <button
                onClick={() => setSortBy('topics')}
                className={`px-3 py-1 rounded text-sm font-medium transition ${
                  sortBy === 'topics'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                By Topics
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedSpeakers.map((speaker) => (
              <div
                key={speaker.speaker_id}
                className={`border-2 rounded-lg p-4 cursor-pointer transition ${
                  selectedSpeaker === speaker.speaker_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() =>
                  setSelectedSpeaker(
                    selectedSpeaker === speaker.speaker_id ? null : speaker.speaker_id
                  )
                }
              >
                {/* Speaker Header */}
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="font-bold text-gray-800 text-lg">
                      {speaker.speaker_name}
                    </div>
                    <div
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border mt-1 ${getRoleColor(
                        speaker.role
                      )}`}
                    >
                      <span>{getRoleIcon(speaker.role)}</span>
                      <span>{speaker.role}</span>
                    </div>
                  </div>
                </div>

                {/* Statistics */}
                <div className="space-y-2">
                  {/* Time Spoken */}
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Time Spoken</span>
                      <span className="font-medium">{speaker.time_spoken_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${speaker.time_spoken_percentage}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatTime(speaker.time_spoken_seconds)}
                    </div>
                  </div>

                  {/* Turns */}
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Turns</span>
                      <span className="font-medium">{speaker.turn_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${speaker.turn_percentage}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {speaker.turn_count} turns
                    </div>
                  </div>

                  {/* Average Turn Duration */}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Avg Turn</span>
                    <span className="font-medium text-gray-800">
                      {formatTime(speaker.avg_turn_duration)}
                    </span>
                  </div>

                  {/* Topics Dominated */}
                  {speaker.topics_dominated.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-xs text-gray-600 mb-2 font-medium">
                        Dominated Topics ({speaker.topics_dominated.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {speaker.topics_dominated.slice(0, 3).map((topic, i) => (
                          <span
                            key={i}
                            className="inline-block px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs"
                            title={topic}
                          >
                            {topic.length > 20 ? topic.substring(0, 20) + '...' : topic}
                          </span>
                        ))}
                        {speaker.topics_dominated.length > 3 && (
                          <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            +{speaker.topics_dominated.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Speaker Details */}
        {selectedSpeaker && analytics.speakers[selectedSpeaker] && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {analytics.speakers[selectedSpeaker].speaker_name} - Detailed View
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* All Topics Dominated */}
              <div>
                <h3 className="font-medium text-gray-700 mb-3">All Dominated Topics</h3>
                {analytics.speakers[selectedSpeaker].topics_dominated.length > 0 ? (
                  <div className="space-y-2">
                    {analytics.speakers[selectedSpeaker].topics_dominated.map((topic, i) => (
                      <div key={i} className="bg-gray-50 rounded p-2 text-sm">
                        {topic}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No topics dominated</p>
                )}
              </div>

              {/* Role Description */}
              <div>
                <h3 className="font-medium text-gray-700 mb-3">Role Description</h3>
                <div className={`rounded-lg p-4 border-2 ${getRoleColor(analytics.speakers[selectedSpeaker].role)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{getRoleIcon(analytics.speakers[selectedSpeaker].role)}</span>
                    <span className="font-bold capitalize">{analytics.speakers[selectedSpeaker].role}</span>
                  </div>
                  <p className="text-sm">
                    {analytics.speakers[selectedSpeaker].role === 'facilitator' &&
                      'Speaks frequently with shorter turns, distributed across multiple topics. Likely guiding the conversation.'}
                    {analytics.speakers[selectedSpeaker].role === 'contributor' &&
                      'Speaks extensively with longer turns, often dominating specific topics. Primary content contributor.'}
                    {analytics.speakers[selectedSpeaker].role === 'observer' &&
                      'Speaks infrequently with brief turns. Participates minimally in the conversation.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Timeline Visualization */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Speaker Timeline</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {analytics.timeline.map((segment, i) => {
              const speaker = analytics.speakers[segment.speaker_id];
              return (
                <div key={i} className="flex items-center gap-3">
                  {/* Speaker Change Indicator */}
                  {segment.is_speaker_change && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  )}
                  {!segment.is_speaker_change && <div className="w-2"></div>}

                  {/* Timeline Bar */}
                  <div className="flex-1 flex items-center gap-2">
                    <div className={`text-xs font-medium px-2 py-1 rounded ${
                      speaker ? getRoleColor(speaker.role) : 'bg-gray-100 text-gray-800'
                    }`}>
                      {segment.speaker_name}
                    </div>
                    <div className="flex-1 bg-gray-100 rounded h-6 relative overflow-hidden">
                      <div
                        className={`h-full ${
                          speaker?.role === 'facilitator' ? 'bg-blue-400' :
                          speaker?.role === 'contributor' ? 'bg-green-400' :
                          'bg-gray-400'
                        }`}
                        style={{
                          width: `${Math.min(segment.duration_seconds * 2, 100)}%`,
                        }}
                      ></div>
                      <div className="absolute inset-0 flex items-center px-2">
                        <span className="text-xs text-gray-700 truncate">
                          {segment.text_preview}
                        </span>
                      </div>
                    </div>
                    {segment.timestamp_start !== null && (
                      <div className="text-xs text-gray-500 w-16 text-right">
                        {formatTime(segment.timestamp_start)}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
