import { useState } from "react";
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


const CORE_API_URL =
  import.meta.env.VITE_CORE_API_URL || CORE_API_URL;

type Status = "idle" | "connecting" | "connected" | "error";

/**
 * Demo18CallButton provides start/stop controls for a voice engine session.
 */
const Demo18CallButton = () => {
  const [status, setStatus] = useState<Status>("idle");

  const startSession = async () => {
    setStatus("connecting");
    try {
      const res = await fetch(`${CORE_API_URL}/voice/session/start`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to start");
      setStatus("connected");
    } catch (err) {
      // Reason: network errors should surface as user-visible feedback
      setStatus("error");
    }
  };

  const stopSession = async () => {
    try {
      await fetch(`${CORE_API_URL}/voice/session/stop`, { method: "POST" });
    } finally {
      setStatus("idle");
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <div className="flex gap-2">
        <button
          onClick={startSession}
          disabled={status === "connecting" || status === "connected"}
          className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
        >
          Start Session
        </button>
        <button
          onClick={stopSession}
          disabled={status !== "connected"}
          className="px-4 py-2 rounded bg-red-600 text-white disabled:opacity-50"
        >
          Stop Session
        </button>
      </div>
      <div className="text-sm">
        {status === "connecting" && (
          <span className="text-yellow-600">Connecting…</span>
        )}
        {status === "connected" && (
          <span className="text-green-600">Connected</span>
        )}
        {status === "error" && <span className="text-red-600">Error</span>}
      </div>
    </div>
  );
};

export default Demo18CallButton;
