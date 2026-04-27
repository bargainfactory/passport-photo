"use client";

import { Shield, Lock, Fingerprint, Globe, ChevronDown } from "lucide-react";
import { useTranslation, LOCALES, LOCALE_NAMES, type Locale } from "@/lib/i18n";
import { useState, useRef, useEffect } from "react";

export default function Header() {
  const { t, locale, setLocale } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

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

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-5">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Shield className="h-3.5 w-3.5 text-accent-300" />
                <span>{t("header.secure")}</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Lock className="h-3.5 w-3.5 text-accent-300" />
                <span>{t("header.encrypted")}</span>
              </div>
            </div>

            {/* Language switcher */}
            <div ref={ref} className="relative">
              <button
                onClick={() => setOpen(!open)}
                className="flex items-center gap-1.5 rounded-lg border border-[rgba(0,212,255,0.1)] bg-deep-100 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:border-[rgba(0,212,255,0.2)] transition-colors"
              >
                <Globe className="h-3.5 w-3.5 text-accent-300" />
                {LOCALE_NAMES[locale]}
                <ChevronDown className={`h-3 w-3 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`} />
              </button>
              {open && (
                <div className="absolute right-0 top-full mt-1 z-50 rounded-lg border border-[rgba(0,212,255,0.12)] bg-deep-100 shadow-glass-lg max-h-72 overflow-y-auto w-40">
                  {LOCALES.map((l) => (
                    <button
                      key={l}
                      onClick={() => { setLocale(l as Locale); setOpen(false); }}
                      className={`flex items-center w-full px-3 py-2 text-xs transition-colors ${
                        locale === l
                          ? "bg-accent-50 text-accent-300 font-semibold"
                          : "text-slate-300 hover:bg-accent-50"
                      }`}
                    >
                      {LOCALE_NAMES[l as Locale]}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
