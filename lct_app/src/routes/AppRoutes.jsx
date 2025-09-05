import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import NewConversation from "../pages/NewConversation";
import ViewConversation from "../pages/ViewConversation";
import Browse from "../pages/Browse";
import Login from "../pages/Login";
import ProtectedRoute from "../components/ProtectedRoute";
import MathTest from "../components/MathTest";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={
        <ProtectedRoute>
          <Home />
        </ProtectedRoute>
      } />
      <Route path="/login" element={<Login />} />
      <Route path="/new" element={
        <ProtectedRoute>
          <NewConversation />
        </ProtectedRoute>
      } />
      <Route path="/browse" element={
        <ProtectedRoute>
          <Browse />
        </ProtectedRoute>
      } />
      <Route path="/conversation/:conversationId" element={
        <ProtectedRoute>
          <ViewConversation />
        </ProtectedRoute>
      } />
      <Route path="/math-test" element={
        <ProtectedRoute>
          <MathTest />
        </ProtectedRoute>
      } />
    </Routes>
  );
}