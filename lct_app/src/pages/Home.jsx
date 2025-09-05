import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import AuthButton from "../components/AuthButton";

export default function Home() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white px-4">
      {/* Auth Button in top right */}
      <div className="absolute top-6 right-6">
        <AuthButton />
      </div>

      {/* Welcome Message */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Live Conversational Threads</h1>
        {currentUser && (
          <p className="text-xl opacity-90">
            Welcome back, {currentUser.displayName?.split(' ')[0]}!
          </p>
        )}
      </div>

      {/* Navigation Buttons */}
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

        {/* <button
          onClick={() => navigate("/math-test")}
          className="w-full px-6 py-3 bg-blue-500 hover:bg-blue-700 active:bg-blue-800 rounded-2xl shadow-lg text-white text-lg transition-all duration-200"
        >
          Test LaTeX Math
        </button> */}
      </div>

      {/* Sign in prompt for unauthenticated users */}
      {!currentUser && (
        <div className="mt-8 text-center">
          <p className="text-lg opacity-80 mb-4">
            Sign in to save and manage your conversations
          </p>
          <button
            onClick={() => navigate("/login")}
            className="px-6 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-xl border border-white/30 hover:border-white/40 transition-all duration-200"
          >
            Get Started
          </button>
        </div>
      )}
    </div>
  );
}