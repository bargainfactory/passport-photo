"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-deep">
      <div className="glass rounded-2xl p-8 max-w-lg text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="h-7 w-7 text-red-400" />
        </div>
        <h2 className="text-lg font-bold text-white mb-2">Application Error</h2>
        <pre className="text-red-400/80 text-sm whitespace-pre-wrap max-w-[60ch] mx-auto mb-4 font-mono">
          {error.message}
        </pre>
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 btn-glow rounded-lg px-5 py-2.5 text-sm font-bold text-white"
        >
          <RotateCcw className="h-4 w-4" /> Try again
        </button>
      </div>
    </div>
  );
}
