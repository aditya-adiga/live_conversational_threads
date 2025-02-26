import { useState, useRef } from "react";

export default function Input() {
  const [text, setText] = useState("");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null); // Reference for hidden file input

  // Handle Text File Upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];

    if (file) {
      if (file.type === "text/plain") {
        setFileName(file.name); // Show filename
        const reader = new FileReader();
        reader.onload = (e) => setText(e.target.result); // Read and set text
        reader.readAsText(file);
      } else {
        alert("Invalid file format! Please upload a .txt file.");
      }
    }
  };

  // Handle Text Change & Remove Uploaded File Name
  const handleTextChange = (e) => {
    setText(e.target.value);
    setFileName(""); // Clear uploaded file name when text is modified
  };

  return (
    <div className="sticky bottom-0 w-full bg-transparent backdrop--lg p-2">
      <div className="max-w-4xl mx-auto flex items-center space-x-3 bg-white rounded-xl shadow-md p-3">
        {/* Upload Button */}
        <button
          className="p-2 bg-gray-300 text-gray-700 rounded-lg text-sm font-semibold shadow-md hover:bg-gray-400 active:scale-95 transition"
          onClick={() => fileInputRef.current.click()} // Click hidden file input
        >
          📂
        </button>

        {/* Hidden File Input (Only for .txt files) */}
        <input
          type="file"
          accept=".txt"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileUpload}
        />

        {/* Text Input Field */}
        <textarea
          className="flex-grow p-6 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none placeholder-gray-400 text-gray-900"
          placeholder="Enter or upload Transcript..."
          value={text}
          rows="1"
          onChange={handleTextChange} // Call updated handler
        />

        {/* Send Button */}
        <button
          className="p-2 bg-indigo-500 text-white rounded-lg text-lg font-bold shadow-lg 
                    hover:bg-indigo-600 active:scale-95 transition"
        >
          🚀
        </button>
      </div>

      {/* Show Uploaded File Name (Only if No Edits Have Been Made) */}
      {fileName && (
        <p className="text-sm text-gray-300 text-center font-semibold mt-1">
          Uploaded: {fileName}
        </p>
      )}
    </div>
  );
}