"use client";

import { Shield, Lock, Zap, Fingerprint } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="mt-auto border-t border-[rgba(0,212,255,0.06)] bg-[rgba(5,10,20,0.6)]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent-300 to-accent-500">
              <Fingerprint className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-sm font-bold tracking-tight">
              <span className="text-white">Visage</span>
              <span className="gradient-text">Pass</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-5 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-accent-300/50" />
              {t("footer.processedLocally")}
            </div>
            <div className="flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-accent-300/50" />
              {t("footer.neverStored")}
            </div>
            <div className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-accent-300/50" />
              {t("footer.aiPowered")}
            </div>
          </div>

          <p className="text-[11px] text-slate-600">
            {t("footer.copyright", { year: String(new Date().getFullYear()) })}
          </p>
        </div>
      </div>
    </footer>
  );
}
