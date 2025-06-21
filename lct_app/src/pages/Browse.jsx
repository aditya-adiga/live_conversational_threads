import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "";

export default function Browse() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const handleView = (conversationId) => {
    navigate(`/conversation/${conversationId}`);
    };

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await fetch(`${API_URL}/conversations/`);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); //sort based on time

        setConversations(data);
      } catch (err) {
        console.error("Error fetching conversations:", err.message);
        setError("Failed to load saved conversations.");
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="w-full px-4 py-6 bg-transparent flex items-center justify-between">
        {/* Back Button */}
        <button
          onClick={() => navigate("/")}
          className="px-4 py-2 bg-white text-blue-600 font-semibold rounded-lg shadow hover:bg-blue-100 transition text-sm md:text-base"
        >
          ⬅ Back
        </button>

        {/* Title */}
        <h1 className="text-xl md:text-3xl font-bold text-center flex-grow">
          Saved Conversations
        </h1>
      </div>
      {/* <h2 className="text-3xl font-bold mb-6 text-center">Saved Conversations</h2> */}

      {loading ? (
        <p className="text-center text-gray-600">Loading conversations...</p>
      ) : error ? (
        <p className="text-center text-red-600">{error}</p>
      ) : conversations.length === 0 ? (
        <p className="text-center text-gray-500">No saved conversations found.</p>
      ) : (
        <div className="space-y-4 max-h-[80vh] overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.file_id}
              className="bg-white rounded-xl shadow p-4 hover:shadow-md transition"
            >
              <h3 className="text-xl text-black font-semibold">{conv.file_name}</h3>
              <p className="text-sm text-gray-500">ID: {conv.file_id}</p>
              <p className="text-sm text-gray-500">Number of Nodes: {conv.no_of_nodes}</p>
              <p className="text-sm text-green-600">{conv.message}</p>
              <p className="text-sm text-gray-400">  Created at: {new Date(conv.created_at).toLocaleString()} </p>

              <button
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                onClick={() => {
                  handleView(conv.file_id)
                }}
              >
                View
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}