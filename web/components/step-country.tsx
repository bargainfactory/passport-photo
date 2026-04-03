"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe, Search, ChevronDown, Sparkles, Zap, Printer,
  Ruler, Palette, UserCircle, Glasses, X, Check,
} from "lucide-react";
import { COUNTRIES, getSpec, mmToPx, type CountrySpec } from "@/lib/countries";
import { cn } from "@/lib/utils";

interface Props {
  onNext: (country: CountrySpec, docType: "passport" | "visa") => void;
}

export default function StepCountry({ onNext }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<CountrySpec | null>(null);
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

  // Close dropdown on outside click
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Hero */}
      <div className="hero-gradient rounded-2xl px-6 py-12 sm:px-12 sm:py-16 text-center mb-8 overflow-hidden relative">
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: "radial-gradient(circle at 20% 80%, rgba(0,212,255,0.3) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0,212,255,0.2) 0%, transparent 50%)",
          }}
        />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6 }}
          className="relative z-10"
        >
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4 tracking-tight text-balance">
            Professional Passport &amp; Visa
            <br />
            <span className="gradient-text-light">Photos in Seconds</span>
          </h1>
          <p className="text-slate-300 text-base sm:text-lg max-w-xl mx-auto mb-8 leading-relaxed">
            AI-powered compliance for 34+ countries. Upload a selfie, get a
            government-ready photo instantly.
          </p>

          {/* Trust badges */}
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              { icon: Globe, text: "34+ Countries" },
              { icon: Sparkles, text: "AI Background Removal" },
              { icon: Printer, text: "300 DPI Print-Ready" },
              { icon: Zap, text: "Instant Processing" },
            ].map(({ icon: Icon, text }) => (
              <div
                key={text}
                className="flex items-center gap-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 px-3 py-1.5 text-xs font-medium text-white/90"
              >
                <Icon className="h-3.5 w-3.5 text-teal-400" />
                {text}
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Selector */}
        <div className="lg:col-span-2 space-y-5">
          <div className="glass rounded-xl p-6 shadow-glass">
            <h2 className="text-lg font-bold text-navy-600 mb-4">
              Choose Your Country
            </h2>

            {/* Searchable dropdown */}
            <div ref={dropdownRef} className="relative mb-4">
              <div
                className={cn(
                  "flex items-center gap-2 rounded-lg border bg-white px-3 py-2.5 cursor-text transition-all",
                  open
                    ? "border-teal-400 ring-2 ring-teal-400/20"
                    : "border-slate-200 hover:border-slate-300"
                )}
                onClick={() => {
                  setOpen(true);
                  inputRef.current?.focus();
                }}
              >
                {selected && !open ? (
                  <>
                    <span className="text-xl leading-none">{selected.flag}</span>
                    <span className="flex-1 text-sm font-medium text-navy-600">
                      {selected.name}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); setSelected(null); setSearch(""); }}
                      className="p-0.5 rounded hover:bg-slate-100"
                    >
                      <X className="h-3.5 w-3.5 text-slate-400" />
                    </button>
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 text-slate-400 flex-shrink-0" />
                    <input
                      ref={inputRef}
                      value={search}
                      onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
                      onFocus={() => setOpen(true)}
                      placeholder="Search countries..."
                      className="flex-1 text-sm outline-none bg-transparent placeholder:text-slate-400"
                    />
                    <ChevronDown className={cn("h-4 w-4 text-slate-400 transition-transform", open && "rotate-180")} />
                  </>
                )}
              </div>

              {/* Dropdown */}
              <AnimatePresence>
                {open && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.98 }}
                    transition={{ duration: 0.15 }}
                    className="absolute z-30 top-full left-0 right-0 mt-1 rounded-lg border border-slate-200 bg-white shadow-glass-lg max-h-64 overflow-y-auto"
                  >
                    {filtered.length === 0 ? (
                      <p className="px-3 py-4 text-sm text-slate-400 text-center">
                        No countries found
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
                            "flex items-center gap-2.5 w-full px-3 py-2 text-left text-sm hover:bg-teal-50 transition-colors",
                            selected?.name === c.name && "bg-teal-50"
                          )}
                        >
                          <span className="text-lg leading-none">{c.flag}</span>
                          <span className="font-medium text-navy-600">{c.name}</span>
                          <span className="ml-auto text-xs text-slate-400">{c.region}</span>
                        </button>
                      ))
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Document type */}
            <label className="text-sm font-semibold text-navy-600 mb-2 block">
              Document Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(["passport", "visa"] as const).map((dt) => (
                <button
                  key={dt}
                  onClick={() => setDocType(dt)}
                  className={cn(
                    "rounded-lg border py-2.5 text-sm font-semibold capitalize transition-all",
                    docType === dt
                      ? "border-teal-400 bg-teal-50 text-teal-700 ring-2 ring-teal-400/20"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  )}
                >
                  {dt}
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
                "mt-6 w-full rounded-lg py-3 text-sm font-bold transition-all",
                selected
                  ? "bg-gradient-to-r from-navy-600 to-navy-500 text-white shadow-lg hover:shadow-xl"
                  : "bg-slate-100 text-slate-400 cursor-not-allowed"
              )}
            >
              Continue to Upload &rarr;
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
                className="glass rounded-xl p-6 shadow-glass border-glow"
              >
                {/* Header */}
                <div className="flex items-center gap-3 mb-5 pb-4 border-b border-slate-100">
                  <span className="text-3xl">{selected.flag}</span>
                  <div>
                    <h3 className="text-lg font-bold text-navy-600">
                      {selected.name}
                    </h3>
                    <p className="text-sm text-slate-500 capitalize">
                      {docType} Photo Requirements
                    </p>
                  </div>
                </div>

                {/* Specs grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Size */}
                  <SpecItem
                    icon={<Ruler className="h-4 w-4" />}
                    label="Photo Size"
                    value={`${spec.width_mm} \u00d7 ${spec.height_mm} mm`}
                    sub={`${pxW} \u00d7 ${pxH} px @ 300 DPI`}
                  />

                  {/* Background */}
                  <SpecItem
                    icon={<Palette className="h-4 w-4" />}
                    label="Background"
                    value={
                      <div className="flex items-center gap-2">
                        <div
                          className="h-5 w-5 rounded border border-slate-200"
                          style={{
                            background: `rgb(${spec.bg_color[0]},${spec.bg_color[1]},${spec.bg_color[2]})`,
                          }}
                        />
                        <span>
                          RGB({spec.bg_color[0]}, {spec.bg_color[1]},{" "}
                          {spec.bg_color[2]})
                        </span>
                      </div>
                    }
                  />

                  {/* Head height */}
                  <SpecItem
                    icon={<UserCircle className="h-4 w-4" />}
                    label="Head Height"
                    value={`${spec.head_pct[0]}\u2013${spec.head_pct[1]}% of photo`}
                  />

                  {/* Expression */}
                  <SpecItem
                    icon={
                      <span className="text-sm leading-none">&#128528;</span>
                    }
                    label="Expression"
                    value={selected.expression}
                  />

                  {/* Glasses */}
                  <SpecItem
                    icon={<Glasses className="h-4 w-4" />}
                    label="Glasses"
                    value={
                      <span className="flex items-center gap-1.5">
                        {selected.glasses ? (
                          <Check className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <X className="h-4 w-4 text-red-500" />
                        )}
                        {selected.glasses
                          ? "Allowed if eyes visible"
                          : "Not allowed"}
                      </span>
                    }
                  />

                  {/* Headgear */}
                  <SpecItem
                    icon={
                      <span className="text-sm leading-none">&#129493;</span>
                    }
                    label="Headgear"
                    value={
                      <span className="flex items-center gap-1.5">
                        {selected.headgear ? (
                          <Check className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <X className="h-4 w-4 text-red-500" />
                        )}
                        {selected.headgear
                          ? "Allowed (religious/medical)"
                          : "Not allowed"}
                      </span>
                    }
                  />
                </div>

                {/* Notes */}
                {selected.notes && (
                  <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-600 leading-relaxed">
                    <span className="font-semibold text-navy-600">Note:</span>{" "}
                    {selected.notes}
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass rounded-xl p-10 shadow-glass text-center"
              >
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
                  <Globe className="h-8 w-8 text-slate-300" />
                </div>
                <h3 className="text-lg font-bold text-slate-400 mb-2">
                  Select a Country
                </h3>
                <p className="text-sm text-slate-400 max-w-sm mx-auto">
                  Choose a country from the dropdown to see the exact passport or
                  visa photo requirements.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

/* -- Spec item sub-component -- */
function SpecItem({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50/80 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
        <span className="text-teal-500">{icon}</span>
        {label}
      </div>
      <div className="text-sm font-semibold text-navy-600">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}
