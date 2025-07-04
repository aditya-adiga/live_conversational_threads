import { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import { Mic } from "lucide-react";

import { saveConversationToServer } from "../utils/SaveConversation";

export default function AudioInput({ onDataReceived, onChunksReceived, chunkDict, graphData, conversationId, setConversationId, setMessage, message, fileName, setFileName }) {
  const [recording, setRecording] = useState(false);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  const pingIntervalRef = useRef(null);

  const lastAutoSaveRef = useRef({ graphData: null, chunkDict: null }); //last saved data
  const wasRecording = useRef(false);
  const graphDataFromSocket = useRef(false);

  const fileNameWasReset = useRef(false);

  useEffect(() => {
    if (
      fileNameWasReset.current &&
      graphData &&
      graphData !== lastAutoSaveRef.current.graphData && // 🛡 ensure it's "new"
      graphData?.[0]?.[0]?.node_name
    ) {
      const initialName = graphData[0][0].node_name.replace(/[/:*?"<>|]/g, "");
      setFileName(initialName);
      fileNameWasReset.current = false;
    }
  }, [graphData, setFileName]);

  useEffect(() => {
    if (!graphData || graphDataFromSocket.current) {
      graphDataFromSocket.current = false; // Reset flag
      return;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "graph_data_update", data: graphData })
      );
      logToServer("Sent graphData update to backend.");
    }
  }, [graphData]);

  useEffect(() => {
    if (!graphData || !chunkDict || !fileName) return;
  
    const timeoutId = setTimeout(async () => {
      try {
        await saveConversationToServer({
          fileName,
          graphData,
          chunkDict,
          conversationId,
        });
  
        lastAutoSaveRef.current = { graphData, chunkDict };
      } catch (err) {
        console.error("Silent auto-save failed:", err);
      }
    }, 1000);
  
    return () => clearTimeout(timeoutId);
  }, [graphData, chunkDict, fileName, conversationId]);

  useEffect(() => {
    if (wasRecording.current && !recording) {
      alert("Recording has stopped.");
    }
    wasRecording.current = recording;
  }, [recording]);

  useEffect(() => {
      if (!message) return;
    
      const handleClick = () => setMessage("");
      window.addEventListener("click", handleClick);
      return () => window.removeEventListener("click", handleClick);
    }, [message, setMessage]);

  const logToServer = (message) => { //logging
    console.log("[Client Log]", message);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "client_log", message }));
    }
  };

  const handleFatalError = async () => {
    setRecording(false);
  
    try {
      processorRef.current?.disconnect();
      sourceRef.current?.disconnect();
  
      // Close AudioContext only if it's still open
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        await audioContextRef.current.close();
      }
  
      // Close WebSocket only if it's still open
      if (
        wsRef.current &&
        wsRef.current.readyState === WebSocket.OPEN
      ) {
        wsRef.current.close();
      }
    } catch (e) {
      console.warn("Error during cleanup:", e);
    }
  
    // clear the refs
    processorRef.current = null;
    sourceRef.current = null;
    audioContextRef.current = null;
    wsRef.current = null;

    // Attempt save if data exists
    if (
      lastAutoSaveRef.current.graphData &&
      lastAutoSaveRef.current.chunkDict
    ) {
      setTimeout(() => {
        setMessage?.(`Conversation "${fileName}" saved.`);
      }, 10);
    } else {
      setMessage?.("Recording ended, but no data was received.");
    }
  };

  function downsampleBuffer(buffer, inputSampleRate, outputSampleRate = 16000) { // downsampling higher audio frequency
    if (inputSampleRate < outputSampleRate) {
      throw new Error(`Input sample rate (${inputSampleRate}) is below the required minimum of ${outputSampleRate} Hz`);
    }
  
    if (inputSampleRate === outputSampleRate) return buffer;
  
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
  
    let offsetResult = 0;
    let offsetBuffer = 0;
  
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
  
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
  
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
  
    return result;
  }

  const startRecording = async () => {
    // clear the previous graph and chunk
    onDataReceived?.([]);
    onChunksReceived?.({}); 
    //reset filename
    setFileName?.("");
    fileNameWasReset.current = true;
    //setting conversation ID
    setConversationId?.(crypto.randomUUID());
    // Open microphone
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const audioTrack = stream.getAudioTracks()[0];
    console.log("[CLIENT] Mic track state:", audioTrack.readyState); // 'live' or 'ended'

    audioTrack.onended = () => {
      console.warn("[CLIENT] Microphone track ended unexpectedly");
    };

    // Optional: Poll mic
    const micStatusInterval = setInterval(() => {
      console.log("[CLIENT] Mic readyState (poll):", audioTrack.readyState);
      if (audioTrack.readyState !== "live") {
        console.log("Mic track state changed to: " + audioTrack.readyState);
        clearInterval(micStatusInterval); // stop polling if ended
      }
    }, 5000);

    // Create AudioContext with 16kHz sample rate (AssemblyAI expects 16kHz PCM)
    audioContextRef.current = new AudioContext({ sampleRate: 16000 });
    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);

    // Create a ScriptProcessorNode to access audio buffers
    processorRef.current = audioContextRef.current.createScriptProcessor(8192, 1, 1);

    // Setup WebSocket connection
    const API_BASE = import.meta.env.VITE_API_URL || window.location.origin;
    const WS_URL = API_BASE.replace(/^http/, "ws") + "/ws/audio";
    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setRecording(true);
      logToServer(`AudioContext requested at 16000Hz, actual: ${audioContextRef.current.sampleRate}Hz`); // logging

  //     // Start ping interval
  // pingIntervalRef.current = setInterval(() => {
  //   if (ws.readyState === WebSocket.OPEN) {
  //     ws.send(JSON.stringify({ type: "ping" }));
  //   }
  // }, 5000); // every 5 seconds


      sourceRef.current.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
    
        if (message.type === "existing_json") {
          graphDataFromSocket.current = true; // Set flag before updating state
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
      logToServer(`WebSocket error: code=${err.code}, reason=${err.reason}`);
      // handleFatalError();
    };
    
    ws.onclose = (e) => {
      logToServer(`WebSocket closed: code=${e.code}, reason=${e.reason}`);

      // Clear ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    
      handleFatalError();
    };
    // Process raw audio data and send as 16-bit PCM
    // Process microphone input
    processorRef.current.onaudioprocess = (e) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      try {
        const inputSampleRate = audioContextRef.current.sampleRate;
        if (inputSampleRate < 16000) {
          throw new Error(`Unsupported sample rate: ${inputSampleRate} Hz`);
        }

        const inputBuffer = e.inputBuffer.getChannelData(0);
        const resampled = downsampleBuffer(inputBuffer, inputSampleRate, 16000);

        const pcmData = new Int16Array(resampled.length);
        for (let i = 0; i < resampled.length; i++) {
          let s = Math.max(-1, Math.min(1, resampled[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        ws.send(pcmData.buffer);
      } catch (err) {
        console.error("Error during audio processing:", err);
        logToServer(`Audio processing error: ${err.message}`);
      }
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
  
      // Save after everything is closed and flushed
      if (
        lastAutoSaveRef.current.graphData &&
        lastAutoSaveRef.current.chunkDict
      ) {
        setTimeout(() => {
          setMessage?.(`Conversation "${fileName}" saved.`);
          resolve();
        }, 10);
      } else {
        setMessage?.("Recording ended, but no data was received.");
        resolve();
      }

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

AudioInput.propTypes = {
  onDataReceived: PropTypes.func,
  onChunksReceived: PropTypes.func,
  chunkDict: PropTypes.object,
  graphData: PropTypes.array,
  conversationId: PropTypes.string,
  setConversationId: PropTypes.func,
  setMessage: PropTypes.func,
  message: PropTypes.string,
  fileName: PropTypes.string,
  setFileName: PropTypes.func,
};