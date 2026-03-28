import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../services/api";
import useBackendStatus from "../hooks/useBackendStatus";
import BackendBanner from "../components/BackendBanner";
import "../styles.css";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { backendUp, retry } = useBackendStatus();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/chat");
    } catch (err) {
      if (err.isNetworkError) {
        setError("Backend is not reachable. Please start the server and try again.");
      } else {
        setError(err.response?.data?.error || "Login failed.");
      }
    }
  };

  return (
    <div className="auth-container">
      <h1>🩺 Medo</h1>
      <p className="subtitle">Your Medical Assistant</p>

      {backendUp === false && <BackendBanner retry={retry} />}

      <form onSubmit={handleSubmit} className="auth-form">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={backendUp === false}>
          {backendUp === false ? "Server Offline" : "Log In"}
        </button>
      </form>
      <p className="switch-link">
        Don't have an account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}
