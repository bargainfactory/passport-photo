"use client";

import { Camera, Shield, Lock, Zap } from "lucide-react";

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-slate-200/60 bg-white/50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col items-center gap-6">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-navy-600 to-navy-500">
              <Camera className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-bold text-navy-600 tracking-tight">
              Photo<span className="text-teal-500">Pass</span>
            </span>
          </div>

          {/* Trust signals */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <div className="flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-slate-400" />
              Photos processed locally
            </div>
            <div className="flex items-center gap-1.5">
              <Lock className="h-4 w-4 text-slate-400" />
              Never stored on servers
            </div>
            <div className="flex items-center gap-1.5">
              <Zap className="h-4 w-4 text-slate-400" />
              AI-powered compliance
            </div>
          </div>

          <p className="text-xs text-slate-400">
            &copy; {new Date().getFullYear()} PhotoPass. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
