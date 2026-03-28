import React, { useRef, useState } from "react";
import { uploadPrescription } from "../services/api";

/**
 * File input that uploads a .txt prescription and shows the result.
 */
export default function PrescriptionUpload({ disabled = false }) {
  const fileRef = useRef(null);
  const [status, setStatus] = useState("");

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setStatus("Uploading…");
    try {
      const res = await uploadPrescription(file);
      setStatus(res.data.message || "Prescription processed!");
    } catch (err) {
      if (err.isNetworkError) {
        setStatus("Server offline. Cannot upload prescription.");
      } else {
        setStatus(err.response?.data?.error || "Upload failed.");
      }
    }
    // Reset so same file can be re-selected
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="prescription-upload">
      <button
        onClick={() => !disabled && fileRef.current?.click()}
        disabled={disabled}
        title={disabled ? "Server offline" : "Upload prescription"}
      >
        📄
      </button>
      <input
        ref={fileRef}
        type="file"
        accept=".txt"
        style={{ display: "none" }}
        onChange={handleUpload}
      />
      {status && <span className="upload-status">{status}</span>}
    </div>
  );
}
