import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import AuthButton from "../components/AuthButton";
import ShareModal from "../components/ShareModal";
import { useAuth } from "../contexts/AuthContext";
import { getUserConversations } from "../utils/api";

export default function Browse() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [viewType, setViewType] = useState('all'); // 'all', 'owned', 'shared'
  
  // Cache for all conversation types
  const [conversationCache, setConversationCache] = useState({
    all: [],
    owned: [],
    shared: [],
    loaded: false
  });
  
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const handleView = (conversationId) => {
    navigate(`/conversation/${conversationId}`);
  };

  const handleShare = (conversation) => {
    setSelectedConversation(conversation);
    setShareModalOpen(true);
  };

  const handleCloseShareModal = () => {
    setShareModalOpen(false);
    setSelectedConversation(null);
  };

  const loadAllConversations = useCallback(async () => {
    // Don't fetch if user is not authenticated
    if (!currentUser) {
      setError("Please sign in to view your conversations.");
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      // Make all three API calls in parallel
      const [allData, ownedData, sharedData] = await Promise.all([
        getUserConversations('all'),
        getUserConversations('owned'),
        getUserConversations('shared')
      ]);

      // Sort all data (backend should handle this but adding as fallback)
      const sortByDate = (data) => data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      const cache = {
        all: sortByDate([...allData]),
        owned: sortByDate([...ownedData]),
        shared: sortByDate([...sharedData]),
        loaded: true
      };

      setConversationCache(cache);
      setConversations(cache[viewType]);
      setError("");
      
    } catch (err) {
      console.error("Error fetching conversations:", err.message);
      if (err.message.includes('Authentication failed')) {
        setError("Authentication failed. Please sign in again.");
      } else {
        setError("Failed to load saved conversations.");
      }
    } finally {
      setLoading(false);
    }
  }, [currentUser, viewType]);

  const handleViewTypeChange = (type) => {
    setViewType(type);
    
    // If data is cached, use it immediately
    if (conversationCache.loaded) {
      setConversations(conversationCache[type]);
    }
  };


  useEffect(() => {
    if (currentUser && !conversationCache.loaded) {
      loadAllConversations();
    }
  }, [currentUser, loadAllConversations, conversationCache.loaded]);

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="w-full px-4 py-6 bg-transparent flex items-center justify-between">
        {/* Back Button */}
        <button
          onClick={() => navigate("/")}
          className="px-4 py-2 bg-white text-blue-600 font-semibold rounded-lg shadow hover:bg-blue-100 transition text-sm md:text-base"
        >
          ⬅ Exit
        </button>

        {/* Title */}
        <h1 className="text-xl md:text-3xl font-bold text-center flex-grow">
          Saved Conversations
        </h1>

        {/* Auth Button */}
        <div className="flex-shrink-0">
          <AuthButton />
        </div>
      </div>
      
      {/* View Toggle Buttons */}
      <div className="w-full px-4 mb-6">
        <div className="flex justify-center space-x-2">
          <button
            onClick={() => handleViewTypeChange('all')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              viewType === 'all' 
                ? 'bg-white text-blue-600 shadow-lg' 
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            All
          </button>
          <button
            onClick={() => handleViewTypeChange('owned')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              viewType === 'owned' 
                ? 'bg-white text-blue-600 shadow-lg' 
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            Owned
          </button>
          <button
            onClick={() => handleViewTypeChange('shared')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              viewType === 'shared' 
                ? 'bg-white text-blue-600 shadow-lg' 
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            Shared
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-center text-gray-600">Loading conversations...</p>
      ) : error ? (
        <p className="text-center text-red-600">{error}</p>
      ) : conversations.length === 0 ? (
        <p className="text-center text-gray-500">
          No {viewType === 'all' ? '' : viewType} conversations found.
        </p>
      ) : (
        <div className="space-y-4 max-h-[80vh] overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.file_id}
              className="bg-white rounded-xl shadow p-4 hover:shadow-md transition"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-xl text-black font-semibold">{conv.file_name}</h3>
                {conv.access_type && (
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    conv.access_type === 'owner' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {conv.access_type === 'owner' ? 'Owned' : 'Shared'}
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-500">ID: {conv.file_id}</p>
              <p className="text-sm text-gray-500">Number of Nodes: {conv.no_of_nodes}</p>
              <p className="text-sm text-green-600">{conv.message}</p>
              <p className="text-sm text-gray-400">Created at: {new Date(conv.created_at).toLocaleString()}</p>

              <div className="mt-4 flex space-x-2">
                <button
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                  onClick={() => handleView(conv.file_id)}
                >
                  View
                </button>
                
                {(conv.access_type === 'owner') && (
                  <button
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center"
                    onClick={() => handleShare(conv)}
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                    </svg>
                    Share
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Share Modal */}
      <ShareModal
        isOpen={shareModalOpen}
        onClose={handleCloseShareModal}
        conversationId={selectedConversation?.file_id}
        conversationName={selectedConversation?.file_name}
      />
    </div>
  );
}