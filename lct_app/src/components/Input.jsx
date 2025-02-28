import { useState, useRef } from "react";

export default function Input({ onDataReceived }) {
  const [text, setText] = useState("");
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false); // Track loading state
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === "text/plain") {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => setText(e.target.result);
      reader.readAsText(file);
    } else {
      alert("Invalid file format! Please upload a .txt file.");
    }
  };

  const handleSubmit = async () => {
    if (!text.trim()) {
      alert("Please enter or upload a transcript!");
      return;
    }
  
    setLoading(true);
    const formData = new FormData();
    formData.append("transcript", text);
  
    try {
      const response = await fetch("http://localhost:8000/generate-context-stream", {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }
  
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let receivedData = []; // Store all received chunks
  
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
  
        const chunk = decoder.decode(value, { stream: true });
        
        // Split response by new lines (since JSONs are sent in lines)
        const jsonObjects = chunk.trim().split("\n");
  
        jsonObjects.forEach((jsonStr) => {
          try {
            const jsonData = JSON.parse(jsonStr);
            receivedData.push(jsonData);
            onDataReceived([...receivedData]); // Send updated data to App.jsx
          } catch (error) {
            console.error("Error parsing JSON:", error);
          }
        });
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to fetch data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sticky bottom-0 w-full bg-transparent p-2">
      <div className="max-w-4xl mx-auto flex items-center space-x-3 bg-white rounded-xl shadow-md p-3">
        {/* Upload Button */}
        <button
          className="p-2 bg-gray-300 text-gray-700 rounded-lg text-sm font-semibold shadow-md hover:bg-gray-400 active:scale-95 transition"
          onClick={() => fileInputRef.current.click()}
        >
          📂
        </button>
        
        {/* Hidden File Input */}
        <input type="file" accept=".txt" ref={fileInputRef} className="hidden" onChange={handleFileUpload} />

        {/* Text Input Field */}
        <textarea
          className="flex-grow p-6 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none placeholder-gray-400 text-gray-900"
          placeholder="Enter or upload transcript..."
          value={text}
          rows="1"
          onChange={(e) => setText(e.target.value)}
        />

        {/* Send Button */}
        <button
          className="p-2 bg-indigo-500 text-white rounded-lg text-lg font-bold shadow-lg 
                    hover:bg-indigo-600 active:scale-95 transition"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "⏳" : "🚀"}
        </button>
      </div>

      {fileName && <p className="text-sm text-gray-300 text-center font-semibold mt-1">Uploaded: {fileName}</p>}
    </div>
  );
}