"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe, Search, ChevronDown, Sparkles, Zap, Printer,
  Ruler, Palette, UserCircle, Glasses, X, Check, ArrowRight, Fingerprint,
} from "lucide-react";
import { COUNTRIES, getSpec, mmToPx, type CountrySpec } from "@/lib/countries";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface Props {
  onNext: (country: CountrySpec, docType: "passport" | "visa") => void;
  defaultCountry?: CountrySpec | null;
}

export default function StepCountry({ onNext, defaultCountry }: Props) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<CountrySpec | null>(defaultCountry ?? null);
  const [docType, setDocType] = useState<"passport" | "visa">("passport");
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(() => {
    if (!search) return COUNTRIES;
    const q = search.toLowerCase();
    return COUNTRIES.filter(
      (c) => c.name.toLowerCase().includes(q) || c.region.toLowerCase().includes(q)
    );
  }, [search]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const spec = selected ? getSpec(selected, docType) : null;
  const pxW = spec ? mmToPx(spec.width_mm) : 0;
  const pxH = spec ? mmToPx(spec.height_mm) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Hero */}
      <div className="hero-gradient rounded-2xl px-6 py-10 sm:px-10 sm:py-12 text-center mb-6 overflow-hidden relative">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 80%, rgba(0,212,255,0.12) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(59,130,246,0.1) 0%, transparent 50%)",
          }}
        />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6 }}
          className="relative z-10"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.05, type: "spring", stiffness: 200, damping: 20 }}
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl btn-glow"
          >
            <Fingerprint className="h-7 w-7 text-white" />
          </motion.div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-3 tracking-tight text-balance">
            {t("country.heroTitle")}
            <br />
            <span className="gradient-text-white">{t("country.heroTitleHighlight")}</span>
          </h1>
          <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto mb-6 leading-relaxed">
            {t("country.heroSubtitle")}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2.5">
            {[
              { icon: Globe, text: t("country.feature.countries") },
              { icon: Sparkles, text: t("country.feature.bgRemoval") },
              { icon: Printer, text: t("country.feature.printReady") },
              { icon: Zap, text: t("country.feature.instant") },
            ].map(({ icon: Icon, text }) => (
              <div
                key={text}
                className="flex items-center gap-1.5 rounded-full bg-white/[0.04] backdrop-blur-sm border border-white/[0.06] px-3 py-1.5 text-[11px] font-medium text-white/80"
              >
                <Icon className="h-3 w-3 text-accent-300" />
                {text}
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: Selector */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass rounded-xl p-5">
            <h2 className="text-base font-bold text-white mb-3">
              {t("country.chooseCountry")}
            </h2>

            {/* Searchable dropdown */}
            <div ref={dropdownRef} className="relative mb-3">
              <div
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-3 py-2.5 cursor-text transition-all bg-deep-100",
                  open
                    ? "border-accent-300/40 ring-2 ring-accent-300/10"
                    : "border-[rgba(0,212,255,0.1)] hover:border-[rgba(0,212,255,0.2)]"
                )}
                onClick={() => {
                  setOpen(true);
                  inputRef.current?.focus();
                }}
              >
                {selected && !open ? (
                  <>
                    <span className="text-xl leading-none">{selected.flag}</span>
                    <span className="flex-1 text-sm font-medium text-white">
                      {selected.name}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); setSelected(null); setSearch(""); }}
                      className="p-0.5 rounded hover:bg-white/10"
                    >
                      <X className="h-3.5 w-3.5 text-slate-500" />
                    </button>
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 text-slate-500 flex-shrink-0" />
                    <input
                      ref={inputRef}
                      value={search}
                      onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
                      onFocus={() => setOpen(true)}
                      placeholder={t("country.searchPlaceholder")}
                      className="flex-1 text-sm outline-none bg-transparent placeholder:text-slate-600 text-white"
                    />
                    <ChevronDown className={cn("h-4 w-4 text-slate-500 transition-transform", open && "rotate-180")} />
                  </>
                )}
              </div>

              <AnimatePresence>
                {open && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.98 }}
                    transition={{ duration: 0.15 }}
                    className="absolute z-30 top-full left-0 right-0 mt-1 rounded-lg border border-[rgba(0,212,255,0.12)] bg-deep-100 shadow-glass-lg max-h-60 overflow-y-auto"
                  >
                    {filtered.length === 0 ? (
                      <p className="px-3 py-4 text-sm text-slate-500 text-center">
                        {t("country.noResults")}
                      </p>
                    ) : (
                      filtered.map((c) => (
                        <button
                          key={c.name}
                          onClick={() => {
                            setSelected(c);
                            setSearch("");
                            setOpen(false);
                          }}
                          className={cn(
                            "flex items-center gap-2.5 w-full px-3 py-2 text-left text-sm transition-colors",
                            "hover:bg-accent-50",
                            selected?.name === c.name && "bg-accent-50"
                          )}
                        >
                          <span className="text-lg leading-none">{c.flag}</span>
                          <span className="font-medium text-white">{c.name}</span>
                          <span className="ml-auto text-xs text-slate-600">{c.region}</span>
                        </button>
                      ))
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Document type */}
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
              {t("country.docType")}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(["passport", "visa"] as const).map((dt) => (
                <button
                  key={dt}
                  onClick={() => setDocType(dt)}
                  className={cn(
                    "rounded-lg border py-2.5 text-sm font-semibold capitalize transition-all",
                    docType === dt
                      ? "border-accent-300/30 bg-accent-50 text-accent-300"
                      : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]"
                  )}
                >
                  {dt === "passport" ? t("country.passport") : t("country.visa")}
                </button>
              ))}
            </div>

            {/* Continue button */}
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              disabled={!selected}
              onClick={() => selected && onNext(selected, docType)}
              className={cn(
                "mt-5 w-full rounded-xl py-3 text-sm font-bold transition-all flex items-center justify-center gap-2",
                selected
                  ? "btn-glow text-white"
                  : "bg-deep-200 text-slate-600 cursor-not-allowed"
              )}
            >
              {t("country.startNow")} <ArrowRight className="h-4 w-4" />
            </motion.button>
          </div>
        </div>

        {/* Right: Spec Panel */}
        <div className="lg:col-span-3">
          <AnimatePresence mode="wait">
            {selected && spec ? (
              <motion.div
                key={selected.name + docType}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="glass rounded-xl p-5 glow-border-active"
              >
                <div className="flex items-center gap-3 mb-4 pb-3 border-b border-[rgba(0,212,255,0.08)]">
                  <span className="text-3xl">{selected.flag}</span>
                  <div>
                    <h3 className="text-base font-bold text-white">
                      {selected.name}
                    </h3>
                    <p className="text-xs text-slate-400 capitalize">
                      {t("country.photoRequirements", { docType: docType === "passport" ? t("country.passport") : t("country.visa") })}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <SpecItem
                    icon={<Ruler className="h-4 w-4" />}
                    label={t("country.photoSize")}
                    value={`${spec.width_mm} \u00d7 ${spec.height_mm} mm`}
                    sub={`${pxW} \u00d7 ${pxH} px @ 300 DPI`}
                  />
                  <SpecItem
                    icon={<Palette className="h-4 w-4" />}
                    label={t("country.background")}
                    value={
                      <div className="flex items-center gap-2">
                        <div
                          className="h-4 w-4 rounded border border-white/10"
                          style={{
                            background: `rgb(${spec.bg_color[0]},${spec.bg_color[1]},${spec.bg_color[2]})`,
                          }}
                        />
                        <span>
                          RGB({spec.bg_color[0]}, {spec.bg_color[1]}, {spec.bg_color[2]})
                        </span>
                      </div>
                    }
                  />
                  <SpecItem
                    icon={<UserCircle className="h-4 w-4" />}
                    label={t("country.headHeight")}
                    value={t("country.headHeightValue", { min: String(spec.head_pct[0]), max: String(spec.head_pct[1]) })}
                  />
                  <SpecItem
                    icon={<span className="text-sm leading-none">&#128528;</span>}
                    label={t("country.expression")}
                    value={selected.expression}
                  />
                  <SpecItem
                    icon={<Glasses className="h-4 w-4" />}
                    label={t("country.glasses")}
                    value={
                      <span className="flex items-center gap-1.5">
                        {selected.glasses ? (
                          <Check className="h-3.5 w-3.5 text-accent-300" />
                        ) : (
                          <X className="h-3.5 w-3.5 text-red-400" />
                        )}
                        {selected.glasses ? t("country.glassesAllowed") : t("country.glassesNotAllowed")}
                      </span>
                    }
                  />
                  <SpecItem
                    icon={<span className="text-sm leading-none">&#129493;</span>}
                    label={t("country.headgear")}
                    value={
                      <span className="flex items-center gap-1.5">
                        {selected.headgear ? (
                          <Check className="h-3.5 w-3.5 text-accent-300" />
                        ) : (
                          <X className="h-3.5 w-3.5 text-red-400" />
                        )}
                        {selected.headgear ? t("country.headgearAllowed") : t("country.headgearNotAllowed")}
                      </span>
                    }
                  />
                </div>

                {selected.notes && (
                  <div className="mt-3 rounded-lg bg-deep-200/50 border border-[rgba(0,212,255,0.06)] p-3 text-xs text-slate-400 leading-relaxed">
                    <span className="font-semibold text-accent-300">{t("country.note")}</span>{" "}
                    {selected.notes}
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass rounded-xl p-8 text-center"
              >
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-deep-200 border border-[rgba(0,212,255,0.08)]">
                  <Globe className="h-7 w-7 text-slate-600" />
                </div>
                <h3 className="text-base font-bold text-slate-400 mb-1">
                  {t("country.selectCountry")}
                </h3>
                <p className="text-sm text-slate-600 max-w-sm mx-auto">
                  {t("country.selectCountryDesc")}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

function SpecItem({
  icon, label, value, sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-deep-200/40 border border-[rgba(0,212,255,0.04)] p-3">
      <div className="flex items-center gap-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
        <span className="text-accent-300">{icon}</span>
        {label}
      </div>
      <div className="text-sm font-semibold text-white/90">{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
