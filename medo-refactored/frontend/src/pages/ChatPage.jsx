import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { sendMessage, getMe, logout } from "../services/api";
import useBackendStatus from "../hooks/useBackendStatus";
import BackendBanner from "../components/BackendBanner";
import UnavailablePlaceholder from "../components/UnavailablePlaceholder";
import ChatMessage from "../components/ChatMessage";
import AudioRecorder from "../components/AudioRecorder";
import PrescriptionUpload from "../components/PrescriptionUpload";
import "../styles.css";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const bottomRef = useRef(null);
  const navigate = useNavigate();
  const { backendUp, retry } = useBackendStatus();

  // Auth guard — only redirect if backend IS up and user is not logged in
  useEffect(() => {
    if (backendUp === true) {
      getMe()
        .then(() => setAuthChecked(true))
        .catch(() => navigate("/"));
    } else if (backendUp === false) {
      // Backend is down — let user stay on the page with degraded view
      setAuthChecked(true);
    }
  }, [backendUp, navigate]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(text);
      const data = res.data;
      const botMsg = {
        role: "bot",
        text: data.response,
        sources: data.sources,
        audio: data.audio_content,
        time: data.inference_time,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorText = err.isNetworkError
        ? "Backend is not reachable. Your message could not be sent."
        : err.response?.data?.error || "Something went wrong.";
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "⚠️ " + errorText },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try { await logout(); } catch { /* ignore if backend down */ }
    navigate("/");
  };

  // Show nothing until we know whether user is authed (or backend is down)
  if (!authChecked) return null;

  const offline = backendUp === false;

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="chat-header">
        <h2>🩺 Medo</h2>
        <div className="header-actions">
          <button onClick={() => navigate("/settings")} className="btn-link">
            ⚙️ Settings
          </button>
          <button onClick={handleLogout} className="btn-link">
            Logout
          </button>
        </div>
      </header>

      {/* Offline banner */}
      {offline && <BackendBanner retry={retry} />}

      {/* Messages */}
      <div className="messages-area">
        {offline && messages.length === 0 && (
          <UnavailablePlaceholder
            feature="Chat"
            detail="The backend server is offline. Messages cannot be sent or received until the server is running."
          />
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} />
        ))}
        {loading && <div className="typing-indicator">Medo is typing…</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="input-area">
        <AudioRecorder onTranscript={(t) => setInput(t)} disabled={offline} />
        <PrescriptionUpload disabled={offline} />
        <input
          type="text"
          placeholder={offline ? "Server offline — cannot send messages" : "Ask Medo a question…"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !offline && send(input)}
          disabled={loading || offline}
        />
        <button onClick={() => send(input)} disabled={loading || !input.trim() || offline}>
          Send
        </button>
      </div>
    </div>
  );
}
