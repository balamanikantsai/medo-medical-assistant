import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../services/api";
import useBackendStatus from "../hooks/useBackendStatus";
import BackendBanner from "../components/BackendBanner";
import "../styles.css";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();
  const { backendUp, retry } = useBackendStatus();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await register(email, username, password);
      setSuccess(res.data.message);
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
      if (err.isNetworkError) {
        setError("Backend is not reachable. Please start the server and try again.");
      } else {
        setError(err.response?.data?.error || "Registration failed.");
      }
    }
  };

  return (
    <div className="auth-container">
      <h1>🩺 Medo — Register</h1>

      {backendUp === false && <BackendBanner retry={retry} />}

      <form onSubmit={handleSubmit} className="auth-form">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password (8+ chars, 1 upper, 1 digit)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
        <button type="submit" disabled={backendUp === false}>
          {backendUp === false ? "Server Offline" : "Register"}
        </button>
      </form>
      <p className="switch-link">
        Already have an account? <Link to="/">Log In</Link>
      </p>
    </div>
  );
}
