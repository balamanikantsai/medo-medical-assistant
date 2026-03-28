import React from "react";

/**
 * A non-blocking banner shown when the backend is unreachable.
 * Accepts an optional `retry` callback to allow manual reconnection.
 */
export default function BackendBanner({ retry }) {
  return (
    <div className="backend-banner">
      <span className="banner-icon">⚠️</span>
      <div className="banner-text">
        <strong>Backend unavailable</strong>
        <p>The server is not reachable. Features that require backend data are disabled.</p>
      </div>
      {retry && (
        <button className="banner-retry" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  );
}
