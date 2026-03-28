import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getSettings, updateLanguage, getMe } from "../services/api";
import useBackendStatus from "../hooks/useBackendStatus";
import BackendBanner from "../components/BackendBanner";
import UnavailablePlaceholder from "../components/UnavailablePlaceholder";
import "../styles.css";

export default function SettingsPage() {
  const [languages, setLanguages] = useState({});
  const [selected, setSelected] = useState("en");
  const [message, setMessage] = useState("");
  const [loadError, setLoadError] = useState(false);
  const navigate = useNavigate();
  const { backendUp, retry } = useBackendStatus();

  useEffect(() => {
    if (backendUp === true) {
      getMe().catch(() => navigate("/"));
      getSettings()
        .then((res) => {
          setLanguages(res.data.supported_languages);
          setSelected(res.data.current_language);
          setLoadError(false);
        })
        .catch((err) => {
          if (err.isNetworkError) setLoadError(true);
        });
    } else if (backendUp === false) {
      setLoadError(true);
    }
  }, [backendUp, navigate]);

  const save = async () => {
    try {
      const res = await updateLanguage(selected);
      setMessage(res.data.message);
    } catch (err) {
      if (err.isNetworkError) {
        setMessage("Backend is not reachable. Cannot save settings.");
      } else {
        setMessage(err.response?.data?.error || "Update failed.");
      }
    }
  };

  const offline = backendUp === false;

  return (
    <div className="settings-container">
      <h2>⚙️ Settings</h2>

      {offline && <BackendBanner retry={retry} />}

      {loadError ? (
        <UnavailablePlaceholder
          feature="Language Settings"
          detail="Cannot load your preferences because the backend is offline. Settings will appear once the server is running."
        />
      ) : (
        <>
          <label htmlFor="lang-select">Preferred Language</label>
          <select
            id="lang-select"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            disabled={offline}
          >
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>

          <button onClick={save} disabled={offline}>
            {offline ? "Server Offline" : "Save"}
          </button>
          {message && <p className="info">{message}</p>}
        </>
      )}

      <button className="btn-link back" onClick={() => navigate("/chat")}>
        ← Back to Chat
      </button>
    </div>
  );
}
