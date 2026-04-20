"use client";

import { Shield, Lock, Fingerprint } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 glass-header">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg btn-glow">
              <Fingerprint className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              <span className="text-white">Visage</span>
              <span className="gradient-text">Pass</span>
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-5">
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Shield className="h-3.5 w-3.5 text-accent-300" />
              <span>Secure & Private</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Lock className="h-3.5 w-3.5 text-accent-300" />
              <span>256-bit Encrypted</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
