import React, { useState, useRef, useEffect, useCallback } from "react";
import { transcribeAudio } from "../services/api";

/**
 * Hold-to-record microphone button.
 * Sends the WebM blob to /api/transcribe and passes the transcript up.
 */
export default function AudioRecorder({ onTranscript, disabled = false }) {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const mediaRecorder = useRef(null);
  const streamRef = useRef(null);
  const chunks = useRef([]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
        mediaRecorder.current.stop();
      }
    };
  }, []);

  const start = useCallback(async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunks.current = [];

      recorder.ondataavailable = (e) => chunks.current.push(e.data);

      recorder.onstop = async () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
        try {
          const res = await transcribeAudio(blob);
          if (res.data.transcript) {
            onTranscript(res.data.transcript);
          }
        } catch (err) {
          const message = err.isNetworkError
            ? "Server offline"
            : "Transcription failed";
          console.warn("Transcription error:", message);
          setError(message);
        }
      };

      mediaRecorder.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      console.warn("Microphone access error:", err.message);
      alert("Microphone access denied or unavailable.");
    }
  }, [onTranscript]);

  const stop = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.stop();
    }
    setRecording(false);
  }, []);

  return (
    <div className="audio-recorder">
      <button
        className={`mic-btn ${recording ? "recording" : ""} ${disabled ? "disabled" : ""}`}
        onMouseDown={disabled ? undefined : start}
        onMouseUp={disabled ? undefined : stop}
        onMouseLeave={disabled ? undefined : stop}
        onTouchStart={disabled ? undefined : start}
        onTouchEnd={disabled ? undefined : stop}
        disabled={disabled}
        title={disabled ? "Server offline" : "Hold to record"}
      >
        🎤
      </button>
      {error && <span className="recorder-error">{error}</span>}
    </div>
  );
}
