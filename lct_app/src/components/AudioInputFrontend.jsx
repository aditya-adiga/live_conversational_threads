import { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import { Mic } from "lucide-react";
import ReconnectingWebSocket from "reconnecting-websocket";

import { saveConversationToServer } from "../utils/SaveConversation";
import { authenticatedFetch } from "../utils/api";

// Batch size constants (matching backend)
const BATCH_SIZE = 4;
const MAX_BATCH_SIZE = 12;

// Function to get temporary AssemblyAI token from backend
async function getTempToken(expiresInSeconds = 600) {
  try {
    const response = await authenticatedFetch("/generate_assemblyai_token/", {
      method: "POST",
      body: JSON.stringify({
        expires_in_seconds: expiresInSeconds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to get temp token: ${response.statusText}`);
    }

    const data = await response.json();
    return data.token;
  } catch (error) {
    console.error("Error fetching temp token:", error);
    throw error;
  }
}

export default function AudioInput({ onDataReceived, onChunksReceived, chunkDict, graphData, conversationId, setConversationId, setMessage, message, fileName, setFileName }) {
  const [recording, setRecording] = useState(false);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  const pingIntervalRef = useRef(null);

  const lastAutoSaveRef = useRef({ graphData: null, chunkDict: null }); //last saved data
  const wasRecording = useRef(false);
  const fileNameWasReset = useRef(false);

  // Refs to track latest props for WebSocket callbacks
  const latestGraphData = useRef(graphData);
  const latestChunkDict = useRef(chunkDict);

  // Locking ref to prevent race conditions
  const isProcessingRef = useRef(false);

  useEffect(() => {
    latestGraphData.current = graphData;
  }, [graphData]);

  useEffect(() => {
    latestChunkDict.current = chunkDict;
  }, [chunkDict]);

  // Transcript accumulation and batching state
  const accumulatorRef = useRef([]);
  const batchSizeRef = useRef(BATCH_SIZE);
  const continueAccumulatingRef = useRef(true);

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

  // Process transcript batch by calling backend API
  const processTranscriptBatch = async (stopAccumulatingFlag = false) => {
    // BLOCK: If already processing, do not start a new request.
    if (isProcessingRef.current) {
      console.log("[CLIENT] Backend busy, queuing batch...");
      return;
    }

    // CHECK: If nothing to process, stop.
    if (accumulatorRef.current.length === 0 && !stopAccumulatingFlag) {
      return;
    }

    try {
      // LOCK
      isProcessingRef.current = true;

      console.log(`[CLIENT] Processing batch of ${accumulatorRef.current.length} transcripts, stopFlag: ${stopAccumulatingFlag}`);
      
      const currentGraphData = latestGraphData.current;
      const currentChunkDict = latestChunkDict.current;

      const response = await authenticatedFetch("/process_transcript/", {
        method: "POST",
        body: JSON.stringify({
          text_batch: accumulatorRef.current,
          stop_accumulating_flag: stopAccumulatingFlag,
          existing_json: (currentGraphData && currentGraphData.length > 0) ? currentGraphData[0] : [],
          chunk_dict: currentChunkDict || {}
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to process transcript: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[CLIENT] Backend response:", result);

      // Update React state with new data
      if (result.new_nodes && result.new_nodes.length > 0) {
        const newNodes = result.new_nodes;
        const currentNodes = (currentGraphData && currentGraphData.length > 0) ? currentGraphData[0] : [];
        const updatedGraph = [...currentNodes, ...newNodes];
        
        console.log(`[CLIENT] Appending ${newNodes.length} new nodes. Total nodes: ${updatedGraph.length}`);
        onDataReceived?.([updatedGraph]);
      }
      
      if (result.chunk_dict) {
        onChunksReceived?.(result.chunk_dict);
      }

      // Handle decision
      if (result.decision === "stop_accumulating") {
        // Reset accumulator with incomplete segment if present
        accumulatorRef.current = result.incomplete_segment ? [result.incomplete_segment] : [];
        batchSizeRef.current = BATCH_SIZE;
        continueAccumulatingRef.current = true;
        console.log("[CLIENT] Batch processed - resetting accumulator");
      } else if (result.decision === "continue_accumulating") {
        // Check if we've hit max batch size
        if (batchSizeRef.current >= MAX_BATCH_SIZE) {
          console.log("[CLIENT] Max batch size reached, forcing segmentation");
          // Increase batch size and keep accumulating
          batchSizeRef.current += BATCH_SIZE;
          console.log(`[CLIENT] Continuing accumulation, new batch size: ${batchSizeRef.current}`);
        }
      }

    } catch (error) {
      console.error("[CLIENT] Error processing transcript batch:", error);
      setMessage?.(`Error processing transcript: ${error.message}`);
    } finally {
      // 6. UNLOCK
      isProcessingRef.current = false;

      // 7. RE-TRIGGER: If we accumulated enough data WHILE we were waiting for the backend, fire again immediately.
      // Or if we hit the max batch size case which we couldn't handle inside the lock.
      const shouldRetrigger = 
        (accumulatorRef.current.length >= batchSizeRef.current) || 
        stopAccumulatingFlag; 
        
      if (shouldRetrigger) {
         setTimeout(() => {
            if (!isProcessingRef.current && accumulatorRef.current.length > 0) {
               const forceStop = (batchSizeRef.current >= MAX_BATCH_SIZE);
               processTranscriptBatch(stopAccumulatingFlag || forceStop); 
            }
         }, 50); 
      }
    }
  };

  // Auto-save conversation data to server after 1 second of inactivity
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

  // Show alert when recording stops
  useEffect(() => {
    if (wasRecording.current && !recording) {
      alert("Recording has stopped.");
    }
    wasRecording.current = recording;
  }, [recording]);

  // Clear message on any click event
  useEffect(() => {
      if (!message) return;
    
      const handleClick = () => setMessage("");
      window.addEventListener("click", handleClick);
      return () => window.removeEventListener("click", handleClick);
    }, [message, setMessage]);


  // Clean up all resources (AudioContext, WebSocket, refs) on fatal error or recording end
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

  // Downsample audio buffer from input sample rate to 16kHz for AssemblyAI
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

  // Initialize recording: setup microphone, AudioContext, WebSocket, and audio processing pipeline
  const startRecording = async () => {
    // clear the previous graph and chunk
    onDataReceived?.([]);
    onChunksReceived?.({}); 
    //reset filename
    setFileName?.("");
    fileNameWasReset.current = true;
    //setting conversation ID
    setConversationId?.(crypto.randomUUID());
    
    // Reset accumulation state
    accumulatorRef.current = [];
    batchSizeRef.current = BATCH_SIZE;
    continueAccumulatingRef.current = true;
    
    try {
      const token = await getTempToken();
      console.log("[CLIENT] Temp token received");

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

      // Setup WebSocket connection to AssemblyAI directly with auto-reconnect
      const WS_URL = `wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&formatted_finals=true&token=${token}`;
      const ws = new ReconnectingWebSocket(WS_URL, [], {
        binaryType: "arraybuffer",
        reconnectInterval: 1000,
        maxReconnectAttempts: 3,
        timeoutInterval: 2000,
      });
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[CLIENT] WebSocket connected to AssemblyAI!");
        setRecording(true);
        console.log(`[CLIENT] AudioContext requested at 16000Hz, actual: ${audioContextRef.current.sampleRate}Hz`);

        sourceRef.current.connect(processorRef.current);
        processorRef.current.connect(audioContextRef.current.destination);
      };

      ws.onmessage = async (event) => {
        try {
          const msg = JSON.parse(event.data);
          console.log("[CLIENT] WebSocket message:", msg);
          
          // Handle AssemblyAI Turn messages - only process when formatted and turn ended
          if (msg.type === "Turn" && msg.turn_is_formatted === true && msg.end_of_turn === true) {
            const transcript = msg.transcript;
            console.log("[TRANSCRIPT]", transcript);
            
            // Add to accumulator
            accumulatorRef.current.push(transcript);
            console.log(`[CLIENT] Accumulator size: ${accumulatorRef.current.length}/${batchSizeRef.current}`);
            
            // Check if we should process the batch
            if (accumulatorRef.current.length >= batchSizeRef.current && continueAccumulatingRef.current) {
              await processTranscriptBatch();
            }
          }
        } catch (e) {
          console.error("[CLIENT] Invalid WebSocket message:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("[CLIENT] WebSocket error:", err);
        setMessage?.("WebSocket error, check the console.");
      };
      
      ws.onclose = (e) => {
        console.log(`[CLIENT] WebSocket closed: code=${e.code}, reason=${e.reason}`);

        // Clear ping interval if any
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        if (e.code === 1000) {
          handleFatalError();
        } else {
          console.log("[CLIENT] Unexpected WebSocket closure, will attempt to reconnect...");
        }
      };

      // Process raw audio data and send as 16-bit PCM
      // Process microphone input
      processorRef.current.onaudioprocess = (e) => {
        // WebSocket.OPEN = 1, ReconnectingWebSocket uses same readyState values
        if (!wsRef.current || wsRef.current.readyState !== 1) return;

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

          wsRef.current.send(pcmData.buffer);
        } catch (err) {
          console.error("[CLIENT] Error during audio processing:", err);
        }
      };
    } catch (error) {
      console.error("[CLIENT] Error during recording setup:", error);
      setMessage?.(`Failed to start recording: ${error.message}`);
      handleFatalError();
      return;
    }
  };

  // Stop recording: close WebSocket and cleanup resources
  const stopRecording = async () => {
    console.log("[CLIENT] Stopping recording...");
    
    try {
      // Process any remaining transcripts in accumulator
      if (accumulatorRef.current.length > 0) {
        // console.log("[CLIENT] Final flush: processing remaining transcripts");
        await processTranscriptBatch(true); // Force stop accumulating
        accumulatorRef.current = [];
      }
      
      // Send termination signal to AssemblyAI
      // WebSocket.OPEN = 1, ReconnectingWebSocket uses same readyState values
      if (wsRef.current && wsRef.current.readyState === 1) {
        wsRef.current.send(JSON.stringify({ terminate_session: true }));
        
        // Give a moment for final messages to arrive
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Cleanup audio resources
      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
      }
      
      if (sourceRef.current) {
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }
      
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      setRecording(false);
      console.log("[CLIENT] Recording stopped successfully");
      
    } catch (error) {
      console.error("[CLIENT] Error stopping recording:", error);
      setRecording(false);
    }
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