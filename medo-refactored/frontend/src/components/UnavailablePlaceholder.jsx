import React from "react";

/**
 * Placeholder shown in place of a component that requires backend data.
 * @param {string} feature - Name of the unavailable feature
 * @param {string} [detail] - Extra explanation
 */
export default function UnavailablePlaceholder({ feature, detail }) {
  return (
    <div className="unavailable-placeholder">
      <span className="placeholder-icon">🔌</span>
      <p className="placeholder-title">{feature} unavailable</p>
      <p className="placeholder-detail">
        {detail || "This feature requires a connection to the backend server."}
      </p>
    </div>
  );
}
