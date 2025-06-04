import { useState, useRef } from "react";
import { Mic } from "lucide-react";

export default function AudioInput({ onDataReceived, onChunksReceived }) {
  const [recording, setRecording] = useState(false);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  const handleFatalError = () => {
    setRecording(false);
  
    try {
      processorRef.current?.disconnect();
      sourceRef.current?.disconnect();
      audioContextRef.current?.close();
      wsRef.current?.close();
    } catch (e) {
      console.warn("Error during cleanup:", e);
    }
  
    wsRef.current = null;
    audioContextRef.current = null;
    processorRef.current = null;
    sourceRef.current = null;
  };

  const startRecording = async () => {
    // Open microphone
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Create AudioContext with 16kHz sample rate (AssemblyAI expects 16kHz PCM)
    audioContextRef.current = new AudioContext({ sampleRate: 16000 });
    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);

    // Create a ScriptProcessorNode to access audio buffers
    processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);

    // Setup WebSocket connection
    const API_BASE = import.meta.env.VITE_API_URL || window.location.origin;
    const WS_URL = API_BASE.replace(/^http/, "ws") + "/ws/audio";
    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setRecording(true);
      sourceRef.current.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
    
        if (message.type === "existing_json") {
          onDataReceived?.(message.data);
        }
      
        if (message.type === "chunk_dict") {
          onChunksReceived?.(message.data);
        }
        console.log("Chunk Dict:", message.data);
    
        if (message.text) {
          console.log("Transcript:", message.text);
          // Optional: Display interim transcript
        }
      } catch (e) {
        console.error("Invalid WebSocket message:", e);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      handleFatalError();
    };
    
    ws.onclose = (e) => {
      console.warn("WebSocket closed unexpectedly:", e);
      handleFatalError();
    };
    // Process raw audio data and send as 16-bit PCM
    processorRef.current.onaudioprocess = (e) => {
      if (ws.readyState !== WebSocket.OPEN) return;

      const inputBuffer = e.inputBuffer.getChannelData(0);
      const pcmData = new Int16Array(inputBuffer.length);

      // Convert Float32 [-1,1] to Int16 PCM
      for (let i = 0; i < inputBuffer.length; i++) {
        let s = Math.max(-1, Math.min(1, inputBuffer[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      ws.send(pcmData.buffer);
    };
  };

  const stopRecording = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
  
    return new Promise((resolve) => {
      // 1. Send flush request
      wsRef.current.send(JSON.stringify({ final_flush: true }));
  
      // 2. Wait for backend ack before closing
      const handleMessage = (event) => {
        const message = JSON.parse(event.data);
  
        if (message.type === "flush_ack") {
          // Flush done — now cleanup
          processorRef.current.disconnect();
          sourceRef.current.disconnect();
          audioContextRef.current.close();
          wsRef.current.close();
          wsRef.current.onmessage = null; // clear handler
          resolve();
        }
        setRecording(false);
        
        // existing json finally
        if (message.type === "existing_json") {
          onDataReceived?.(message.data);
        }
        
        // chunk dict finally
        if (message.type === "chunk_dict") {
          onChunksReceived?.(message.data);
        }
      };
  
      wsRef.current.onmessage = handleMessage;
    });
  };

  return (
    <div className="flex items-center space-x-3">
  <button
        onClick={recording ? stopRecording : startRecording} // Toggle recording state on click
        className={`
          flex items-center justify-center w-20 h-20 rounded-full
          ${
            recording
              ? "bg-gradient-to-tr from-red-500 to-pink-600 shadow-lg"
              : "bg-gradient-to-tr from-green-400 to-purple-800 shadow-md"
          }
          text-white                       // White icon color
          hover:brightness-110             // Slightly brighten on hover
          transition duration-300          // Smooth transition for hover effects
          focus:outline-none               // Remove default focus outline
          focus:ring-4                    // Add a focus ring with width 4px
          focus:ring-purple-400           // Purple colored focus ring for accessibility
        `}
        aria-label={recording ? "Stop recording" : "Start recording"} // Screen reader label
      >
      <Mic size={24} />
    </button>
  </div>
  );
}