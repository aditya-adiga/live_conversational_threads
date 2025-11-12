import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white px-4">
      <h1 className="text-4xl font-bold mb-12 text-center">Live Conversational Threads</h1>

      <div className="flex flex-col gap-6 w-full max-w-xs">
        <button
          onClick={() => navigate("/new")}
          className="w-full px-6 py-3 bg-emerald-500 hover:bg-emerald-700 active:bg-emerald-800 rounded-2xl shadow-lg text-white text-lg transition-all duration-200"
        >
          Start New Conversation
        </button>

        <button
          onClick={() => navigate("/browse")}
          className="w-full px-6 py-3 bg-yellow-500 hover:bg-yellow-700 active:bg-yellow-800 rounded-2xl shadow-lg text-white text-lg transition-all duration-200"
        >
          Browse Conversations
        </button>

        <button
          onClick={() => navigate("/cost-dashboard")}
          className="w-full px-6 py-3 bg-indigo-500 hover:bg-indigo-700 active:bg-indigo-800 rounded-2xl shadow-lg text-white text-lg transition-all duration-200"
        >
          💰 Cost Dashboard
        </button>

        <button
          onClick={() => navigate("/settings")}
          className="w-full px-6 py-3 bg-gray-500 hover:bg-gray-700 active:bg-gray-800 rounded-2xl shadow-lg text-white text-lg transition-all duration-200"
        >
          ⚙️ Settings
        </button>
      </div>
    </div>
  );
}