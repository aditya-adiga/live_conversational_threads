import Input from "./components/Input";
import GraphComponent from "./components/GraphComponent"; // Import GraphComponent

export default function App() {
  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-500 to-purple-600 text-white">
      {/* Header */}
      <div className="text-center p-6">
        <h1 className="text-4xl font-bold">Live Conversational Threads</h1>
      </div>

      {/* Main Graph Area (Takes Up Available Space) */}
      <div className="flex-grow flex justify-center items-center p-6">
        <div className="flex space-x-7 w-full max-w-15xl">
          {/* Structural Flow */}
          <div className="w-1/3 bg-white rounded-lg shadow-lg p-4">
          <h2 className="text-xl font-bold text-gray-800 text-center mb-2">Structural Flow</h2>
            <GraphComponent />
          </div>

          {/* Relational Flow */}
          <div className="w-2/3 bg-white rounded-lg shadow-lg p-4">
          <h2 className="text-xl font-bold text-gray-800 text-center mb-2">Relational Flow</h2>
            <GraphComponent />
          </div>
        </div>
      </div>

      {/* Fixed Chat-Like Input at the Bottom */}
      <div className="sticky bottom-0 w-full shadow-lg p-4">
        <Input />
      </div>
    </div>
  );
}