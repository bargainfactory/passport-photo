"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div style={{ padding: "2rem", fontFamily: "monospace" }}>
      <h2>Application Error</h2>
      <pre style={{ color: "red", whiteSpace: "pre-wrap", maxWidth: "80ch" }}>
        {error.message}
      </pre>
      <pre style={{ color: "#666", whiteSpace: "pre-wrap", maxWidth: "80ch", fontSize: "12px" }}>
        {error.stack}
      </pre>
      <button onClick={() => reset()} style={{ marginTop: "1rem", padding: "0.5rem 1rem" }}>
        Try again
      </button>
    </div>
  );
}
