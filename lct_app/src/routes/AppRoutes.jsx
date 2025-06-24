import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import NewConversation from "../pages/NewConversation";
import ViewConversation from "../pages/ViewConversation";
import Browse from "../pages/Browse";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/new" element={<NewConversation />} />
      <Route path="/browse" element={<Browse />} />
      <Route path="/conversation/:conversationId" element={<ViewConversation />} />
    </Routes>
  );
}