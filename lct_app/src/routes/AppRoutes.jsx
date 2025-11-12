import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import NewConversation from "../pages/NewConversation";
import ViewConversation from "../pages/ViewConversation";
import Browse from "../pages/Browse";
import Analytics from "../pages/Analytics";
import Settings from "../pages/Settings";
import EditHistory from "../pages/EditHistory";
import SimulacraAnalysis from "../pages/SimulacraAnalysis";
import BiasAnalysis from "../pages/BiasAnalysis";
import FrameAnalysis from "../pages/FrameAnalysis";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/new" element={<NewConversation />} />
      <Route path="/browse" element={<Browse />} />
      <Route path="/conversation/:conversationId" element={<ViewConversation />} />
      <Route path="/analytics/:conversationId" element={<Analytics />} />
      <Route path="/edit-history/:conversationId" element={<EditHistory />} />
      <Route path="/simulacra/:conversationId" element={<SimulacraAnalysis />} />
      <Route path="/biases/:conversationId" element={<BiasAnalysis />} />
      <Route path="/frames/:conversationId" element={<FrameAnalysis />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  );
}