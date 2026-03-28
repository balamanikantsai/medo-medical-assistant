/**
 * Axios instance pre-configured for the Flask backend.
 * In development, Create React App proxies /api/* to http://localhost:5000
 * via the "proxy" field in package.json, so we use relative URLs.
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,           // send session cookie
  headers: { "Content-Type": "application/json" },
  timeout: 15000,                  // 15s default — fail fast for quick endpoints
});

/**
 * Response interceptor: normalise network errors so callers can easily
 * distinguish "backend unreachable" from "API returned an error".
 *
 * - Network / timeout errors → err.response is undefined, err.isNetworkError = true.
 * - HTTP errors (4xx/5xx)    → err.response exists as usual.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Mark network-level failures so UI can detect them
      error.isNetworkError = true;
      error.friendlyMessage =
        "Cannot reach the server. Please check if the backend is running.";
    }
    return Promise.reject(error);
  }
);

/** Helper: returns true when back end is reachable (even 401 counts). */
export const ping = async () => {
  try {
    await api.get("/auth/me");
    return true;
  } catch (err) {
    return !!err.response;          // got HTTP status → server is alive
  }
};

/* ── Auth ─────────────────────────────────────────────── */
export const login    = (username, password) => api.post("/auth/login", { username, password });
export const register = (email, username, password) => api.post("/auth/register", { email, username, password });
export const logout   = () => api.post("/auth/logout");
export const getMe    = () => api.get("/auth/me");

/* ── Chat ─────────────────────────────────────────────── */
// Extended timeout for chat — AI responses with thinking can take longer
export const sendMessage = (prompt) => api.post("/chat", { prompt }, { timeout: 120000 });

export const transcribeAudio = (blob) => {
  const form = new FormData();
  form.append("audio_blob", blob, "recording.webm");
  return api.post("/transcribe", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 30000,  // Audio transcription may take longer
  });
};

/* ── Prescription ─────────────────────────────────────── */
export const uploadPrescription = (file) => {
  const form = new FormData();
  form.append("prescriptionFile", file);
  return api.post("/prescription/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,  // Prescription parsing involves LLM + calendar API
  });
};

/* ── Settings ─────────────────────────────────────────── */
export const getSettings    = () => api.get("/settings");
export const updateLanguage = (language) => api.put("/settings/language", { language });

export default api;
