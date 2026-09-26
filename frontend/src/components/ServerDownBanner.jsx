import { useEffect, useState } from "react";

// Shown when the API is unreachable or the database is down (503).
export default function ServerDownBanner() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    const down = (e) => setMessage(e.detail || "The server is not reachable right now. Retrying when you try again.");
    const up = () => setMessage("");
    window.addEventListener("server-down", down);
    window.addEventListener("server-up", up);
    return () => {
      window.removeEventListener("server-down", down);
      window.removeEventListener("server-up", up);
    };
  }, []);

  if (!message) return null;
  return (
    <div role="alert" className="sticky top-0 z-40 bg-amber-500 px-4 py-2 text-center text-sm font-semibold text-white">
      ⚠ {message}
    </div>
  );
}
