"use client";

import { Camera, Shield, Lock } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 glass-dark">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-teal-400">
              <Camera className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white tracking-tight">
              Photo<span className="text-teal-400">Pass</span>
            </span>
          </div>

          {/* Trust signals */}
          <div className="hidden sm:flex items-center gap-5">
            <div className="flex items-center gap-1.5 text-xs text-slate-300">
              <Shield className="h-3.5 w-3.5 text-teal-400" />
              <span>Secure &amp; Private</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-300">
              <Lock className="h-3.5 w-3.5 text-teal-400" />
              <span>256-bit Encrypted</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
