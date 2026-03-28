import { useState, useEffect, useCallback } from "react";
import { getMe } from "../services/api";

/**
 * Custom hook that periodically checks whether the Flask backend is reachable.
 * Returns { backendUp: bool | null, checking: bool, retry: fn }
 *   - null  = haven't checked yet
 *   - true  = reachable
 *   - false = unreachable
 */
export default function useBackendStatus(intervalMs = 30000) {
  const [backendUp, setBackendUp] = useState(null);
  const [checking, setChecking] = useState(true);

  const check = useCallback(async () => {
    setChecking(true);
    try {
      // We use getMe as a lightweight ping — even a 401 means backend is up.
      await getMe();
      setBackendUp(true);
    } catch (err) {
      // If we got any HTTP response the server is alive (e.g. 401 Unauthorized).
      if (err.response) {
        setBackendUp(true);
      } else {
        // Network error / CORS / timeout → backend down
        setBackendUp(false);
      }
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [check, intervalMs]);

  return { backendUp, checking, retry: check };
}
