"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={{ padding: "2rem", fontFamily: "monospace" }}>
        <h1>Something went wrong!</h1>
        <pre style={{ color: "red", whiteSpace: "pre-wrap", maxWidth: "80ch" }}>
          {error.message}
        </pre>
        <pre style={{ color: "#666", whiteSpace: "pre-wrap", maxWidth: "80ch", fontSize: "12px" }}>
          {error.stack}
        </pre>
        <button onClick={() => reset()} style={{ marginTop: "1rem", padding: "0.5rem 1rem" }}>
          Try again
        </button>
      </body>
    </html>
  );
}
