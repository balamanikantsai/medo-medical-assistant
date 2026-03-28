import React, { useRef, useCallback } from "react";

/**
 * Renders a single chat bubble (user or bot).
 * If bot message includes audio, provides a play button.
 */
export default function ChatMessage({ message }) {
  const audioRef = useRef(null);
  const isBot = message.role === "bot";

  const playAudio = useCallback(() => {
    if (!message.audio) return;

    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    try {
      const audio = new Audio(`data:audio/mp3;base64,${message.audio}`);
      audioRef.current = audio;

      audio.play().catch((err) => {
        console.warn("Audio playback failed:", err.message);
      });

      // Cleanup when audio ends
      audio.onended = () => {
        audioRef.current = null;
      };
    } catch (err) {
      console.warn("Failed to create audio:", err.message);
    }
  }, [message.audio]);

  return (
    <div className={`chat-bubble ${isBot ? "bot" : "user"}`}>
      <p>{message.text}</p>

      {isBot && message.sources?.length > 0 && (
        <div className="sources">
          <strong>Sources:</strong>
          <ul>
            {message.sources.map((s, i) => (
              <li key={s.url || i}>
                <a href={s.url} target="_blank" rel="noreferrer">
                  {s.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {isBot && message.audio && (
        <button className="play-btn" onClick={playAudio}>
          🔊 Play
        </button>
      )}

      {isBot && message.time && (
        <span className="meta">{message.time}s</span>
      )}
    </div>
  );
}
