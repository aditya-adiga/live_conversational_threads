import { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import { Video } from "lucide-react";
import { saveConversationToServer } from "../utils/SaveConversation";
import { authenticatedFetch } from "../utils/api";

export default function GoogleMeetInput({ onDataReceived, onChunksReceived, setConversationId, conversationId, setMessage, graphData, chunkDict, fileName, setFileName }) {
  const [meetingUrl, setMeetingUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [botId, setBotId] = useState(null);
  const [error, setError] = useState(null);
  
  const eventSourceRef = useRef(null);
  const lastAutoSaveRef = useRef({ graphData: null, chunkDict: null });
  const fileNameWasReset = useRef(false);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Auto-save conversation data to server after 1 second of inactivity
  useEffect(() => {
    if (!graphData || !chunkDict || !fileName) return;
  
    const timeoutId = setTimeout(async () => {
      try {
        // Check if data actually changed to avoid duplicate saves
        if (lastAutoSaveRef.current.graphData === graphData && lastAutoSaveRef.current.chunkDict === chunkDict) {
            return;
        }

        await saveConversationToServer({
          fileName,
          graphData,
          chunkDict,
          conversationId: conversationId,
        });
  
        lastAutoSaveRef.current = { graphData, chunkDict };
      } catch (err) {
        console.error("Silent auto-save failed:", err);
      }
    }, 1000);
  
    return () => clearTimeout(timeoutId);
  }, [graphData, chunkDict, fileName, conversationId]);

  // Set initial filename from first node name when graphData is received
  useEffect(() => {
    if (
      fileNameWasReset.current &&
      graphData &&
      graphData !== lastAutoSaveRef.current.graphData && 
      graphData?.[0]?.[0]?.node_name
    ) {
      const initialName = graphData[0][0].node_name.replace(/[/:*?"<>|]/g, "");
      setFileName(initialName);
      fileNameWasReset.current = false;
    }
  }, [graphData, setFileName]);

  const startBot = async () => {
    if (!meetingUrl) return;
    
    // Reset state
    onDataReceived?.([]);
    onChunksReceived?.({});
    setFileName?.("");
    fileNameWasReset.current = true;
    setConversationId(crypto.randomUUID());
    
    setIsConnecting(true);
    setError(null);
    
    try {
        const response = await authenticatedFetch("/recall/start_bot", {
            method: "POST",
            body: JSON.stringify({ meeting_url: meetingUrl })
        });
        
        if (!response.ok) {
             const errData = await response.json().catch(() => ({}));
             throw new Error(errData.detail || "Failed to start bot");
        }
        
        const data = await response.json();
        setBotId(data.bot_id);
        setIsConnected(true);
        
        connectSSE(data.bot_id);
        
    } catch (error) {
        console.error("Error starting bot:", error);
        setError(error.message);
        setIsConnecting(false);
    }
  };

  const stopBot = async () => {
      if (!botId) return;
      
      try {
          const response = await authenticatedFetch("/recall/stop_bot", {
              method: "POST",
              body: JSON.stringify({ bot_id: botId })
          });
          
          if (!response.ok) {
              console.error("Failed to stop bot backend");
          }
      } catch (e) {
          console.error("Error stopping bot:", e);
      }
      
      // Cleanup frontend connection
      if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
      }
      setIsConnected(false);
      setIsConnecting(false);
      setBotId(null);
      setMessage?.("Bot stopped.");
  };
  
  const connectSSE = (id) => {
      const API_BASE = import.meta.env.VITE_API_URL || window.location.origin;
      const baseUrl = API_BASE.replace(/\/$/, "");
      const sseUrl = `${baseUrl}/recall/events/${id}`;
      
      console.log("[CLIENT] Connecting SSE:", sseUrl);
      
      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;
      
      eventSource.onopen = () => {
          console.log("[CLIENT] SSE Connected");
          setIsConnecting(false);
      };
      
      eventSource.onmessage = (event) => {
          try {
              const message = JSON.parse(event.data);
              if (message.type === "graph_update") {
                  // Update graph
                  if (message.data) {
                      onDataReceived([message.data]);
                  }
                  if (message.chunks) {
                      onChunksReceived(message.chunks);
                  }
              }
          } catch (e) {
              console.error("Error parsing SSE message:", e);
          }
      };
      
      eventSource.onerror = (err) => {
          console.error("SSE Error:", err);
          // EventSource auto-reconnects, but if it fails permanently we might want to know.
          if (eventSource.readyState === EventSource.CLOSED) {
               setIsConnecting(false);
               setIsConnected(false);
          }
      };
  };

  return (
    <div className="flex flex-col items-center space-y-2 p-4 bg-white rounded-lg shadow-md max-w-md w-full">
       <div className="flex items-center space-x-2 w-full">
           <div className="bg-blue-100 p-2 rounded-full">
               <Video className="text-blue-600" size={20} />
           </div>
           <input 
                type="text" 
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                placeholder="Paste Google Meet URL..."
                className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                disabled={isConnected || isConnecting}
           />
           <button 
                onClick={isConnected ? stopBot : startBot}
                disabled={isConnecting || (!isConnected && !meetingUrl)}
                className={`px-4 py-2 rounded text-sm font-medium text-white transition-colors
                    ${isConnecting || (!isConnected && !meetingUrl)
                        ? "bg-gray-400 cursor-not-allowed" 
                        : isConnected 
                            ? "bg-red-500 hover:bg-red-600"
                            : "bg-blue-600 hover:bg-blue-700"
                    }`}
           >
               {isConnecting ? "..." : isConnected ? "Stop Bot" : "Start"}
           </button>
       </div>
       
       {error && (
           <div className="text-red-500 text-xs w-full text-left px-1">
               {error}
           </div>
       )}
       
       {isConnected && (
           <div className="text-green-600 text-xs w-full text-left px-1 flex items-center">
               <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
               Bot is listening to the meeting...
           </div>
       )}
    </div>
  );
}

GoogleMeetInput.propTypes = {
  onDataReceived: PropTypes.func.isRequired,
  onChunksReceived: PropTypes.func.isRequired,
  setConversationId: PropTypes.func.isRequired,
  conversationId: PropTypes.string,
  setMessage: PropTypes.func,
  graphData: PropTypes.array,
  chunkDict: PropTypes.object,
  fileName: PropTypes.string,
  setFileName: PropTypes.func,
};



