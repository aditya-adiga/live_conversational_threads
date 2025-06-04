import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
// import App from "./App.jsx";
import LiveApp from "./LiveApp.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <LiveApp />
  </StrictMode>
);
