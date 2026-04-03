"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, ArrowRight, ScanFace, Palette, Crop, ShieldCheck,
  Check, X, Loader2, AlertTriangle, RefreshCw, Sun, Sparkles, Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type CountrySpec, getSpec } from "@/lib/countries";

interface Props {
  country: CountrySpec;
  docType: "passport" | "visa";
  imageUrl: string;
  onNext: (processedUrl: string, sheetUrl: string) => void;
  onBack: () => void;
}

interface ValidationCheck {
  check: string;
  passed: boolean;
  message: string;
}

const STAGES = [
  { icon: ScanFace,    label: "Detecting face & features...",  done: "Face & features detected"   },
  { icon: Eye,         label: "Correcting pose & alignment...",done: "Pose & alignment corrected"  },
  { icon: Sun,         label: "Fixing lighting & shadows...",  done: "Lighting & shadows fixed"    },
  { icon: Palette,     label: "Removing background...",        done: "Background removed"          },
  { icon: Sparkles,    label: "Enhancing & retouching...",     done: "Enhanced & retouched"        },
  { icon: Crop,        label: "Cropping to exact specs...",    done: "Cropped to exact specs"      },
  { icon: ShieldCheck, label: "Validating compliance...",      done: "Compliance validated"        },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StepPreview({ country, docType, imageUrl, onNext, onBack }: Props) {
  const [stage, setStage] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [sheetUrl, setSheetUrl] = useState<string | null>(null);
  const [checks, setChecks] = useState<ValidationCheck[]>([]);
  const spec = getSpec(country, docType);

  const runProcessing = useCallback(async () => {
    setStage(0);
    setDone(false);
    setError(null);
    setProcessedUrl(null);
    setSheetUrl(null);
    setChecks([]);

    // Animate stages while the API call runs
    const stageTimers: ReturnType<typeof setTimeout>[] = [];
    let currentStage = 0;
    const advanceStage = () => {
      currentStage++;
      if (currentStage < STAGES.length) {
        setStage(currentStage);
        stageTimers.push(setTimeout(advanceStage, 2500));
      }
    };
    stageTimers.push(setTimeout(advanceStage, 1800));

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);

      const res = await fetch(`${API_URL}/api/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          image_b64: imageUrl,
          width_mm: spec.width_mm,
          height_mm: spec.height_mm,
          bg_color: spec.bg_color,
          head_pct: spec.head_pct,
          eye_line_pct: spec.eye_line_pct,
        }),
      });

      clearTimeout(timeoutId);
      stageTimers.forEach(clearTimeout);

      if (!res.ok) {
        let errMsg = `Server error ${res.status}`;
        try {
          const body = await res.json();
          errMsg = body.detail || errMsg;
        } catch {
          // response wasn't JSON
        }
        throw new Error(errMsg);
      }

      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error("Invalid response from server");
      }

      if (!data.processed_b64 || !data.sheet_b64) {
        throw new Error("Server returned incomplete data");
      }

      setProcessedUrl(data.processed_b64);
      setSheetUrl(data.sheet_b64);
      setChecks(Array.isArray(data.validation) ? data.validation : []);
      setStage(STAGES.length);

      setTimeout(() => setDone(true), 400);
    } catch (err: unknown) {
      stageTimers.forEach(clearTimeout);
      let msg = "Processing failed. Please try again.";
      if (err instanceof Error) {
        if (err.name === "AbortError") {
          msg = "Processing timed out. Try with a smaller or clearer photo.";
        } else if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
          msg = "Cannot reach the processing server. Make sure the backend is running on port 8000.";
        } else {
          msg = err.message;
        }
      }
      setError(msg);
    }
  }, [imageUrl, spec]);

  useEffect(() => {
    runProcessing();
  }, [runProcessing]);

  const passedCount = checks.filter((c) => c.passed).length;
  const allPassed = checks.length > 0 && checks.every((c) => c.passed);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-navy-600 transition-colors mb-4"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Upload
      </button>

      {/* Country badge */}
      <div className="inline-flex items-center gap-2 rounded-full bg-navy-600/5 border border-navy-600/10 px-3 py-1 text-sm font-semibold text-navy-600 mb-6">
        <span className="text-base">{country.flag}</span>
        {country.name} &mdash; {docType.charAt(0).toUpperCase() + docType.slice(1)}
      </div>

      <AnimatePresence mode="wait">
        {error ? (
          /* ─── Error state ─── */
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass rounded-xl p-8 shadow-glass text-center max-w-lg mx-auto"
          >
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100">
              <AlertTriangle className="h-7 w-7 text-red-500" />
            </div>
            <h3 className="text-lg font-bold text-navy-600 mb-2">
              Processing Error
            </h3>
            <p className="text-sm text-slate-500 mb-5 max-w-sm mx-auto">
              {error}
            </p>
            <div className="flex items-center justify-center gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={runProcessing}
                className="flex items-center gap-2 rounded-lg bg-navy-600 px-5 py-2.5 text-sm font-bold text-white"
              >
                <RefreshCw className="h-4 w-4" /> Retry
              </motion.button>
              <button
                onClick={onBack}
                className="rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Upload Different Photo
              </button>
            </div>
          </motion.div>
        ) : !done ? (
          /* ─── Processing animation ─── */
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass rounded-xl p-8 shadow-glass max-w-xl mx-auto"
          >
            {/* Photo thumbnail with pulsing ring */}
            <div className="relative mx-auto mb-8 h-36 w-36">
              <motion.div
                animate={{ scale: [1, 1.08, 1], opacity: [0.3, 0.5, 0.3] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-[-6px] rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-300"
              />
              <div className="relative h-full w-full rounded-2xl overflow-hidden border-2 border-white shadow-lg">
                <img src={imageUrl} alt="" className="h-full w-full object-cover" />
                <div className="absolute inset-0 bg-navy-600/20 flex items-center justify-center backdrop-blur-[1px]">
                  <Loader2 className="h-10 w-10 text-white animate-spin drop-shadow-lg" />
                </div>
              </div>
            </div>

            <h3 className="text-center text-base font-bold text-navy-600 mb-1">
              AI Processing Your Photo
            </h3>
            <p className="text-center text-xs text-slate-400 mb-6">
              Transforming your selfie into a professional passport photo
            </p>

            {/* Stage list */}
            <div className="space-y-2.5 max-w-sm mx-auto">
              {STAGES.map((s, i) => {
                const Icon = s.icon;
                const isComplete = i < stage;
                const isCurrent = i === stage;
                return (
                  <motion.div
                    key={s.label}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.07 }}
                    className="flex items-center gap-3"
                  >
                    <div className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-500",
                      isComplete && "bg-emerald-100 text-emerald-600 shadow-sm",
                      isCurrent && "bg-gradient-to-br from-teal-100 to-cyan-100 text-teal-600 shadow-sm",
                      !isComplete && !isCurrent && "bg-slate-50 text-slate-300"
                    )}>
                      {isComplete ? (
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 500, damping: 15 }}>
                          <Check className="h-4 w-4" />
                        </motion.div>
                      ) : isCurrent ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Icon className="h-4 w-4" />
                      )}
                    </div>
                    <span className={cn(
                      "text-sm font-medium transition-colors duration-500",
                      isComplete && "text-emerald-700",
                      isCurrent && "text-navy-600",
                      !isComplete && !isCurrent && "text-slate-300"
                    )}>
                      {isComplete ? s.done : s.label}
                    </span>
                  </motion.div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="mt-6 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
              <motion.div
                initial={{ width: "0%" }}
                animate={{ width: `${Math.min((stage / STAGES.length) * 100, 95)}%` }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
                className="h-full rounded-full bg-gradient-to-r from-teal-500 via-cyan-400 to-teal-400"
              />
            </div>

            <p className="text-xs text-slate-400 mt-4 text-center">
              AI is enhancing your photo. This may take 15&ndash;30 seconds&hellip;
            </p>
          </motion.div>
        ) : (
          /* ─── Results ─── */
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Before / After */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-6">
              {/* Original */}
              <div className="glass rounded-xl p-4 shadow-glass">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Original
                </p>
                <div className="rounded-lg overflow-hidden bg-slate-50 flex items-center justify-center" style={{ minHeight: "12rem" }}>
                  <img src={imageUrl} alt="Original" className="rounded-lg w-full object-contain max-h-72" />
                </div>
              </div>

              {/* Processed */}
              <div className="rounded-xl p-4 shadow-glass border-2 border-teal-200 bg-gradient-to-br from-white to-teal-50/30">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold text-teal-700 uppercase tracking-wider">
                    AI Enhanced
                  </p>
                  <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                    <Sparkles className="h-3 w-3" /> Studio Quality
                  </span>
                </div>
                <div className="rounded-lg overflow-hidden bg-white flex items-center justify-center" style={{ minHeight: "12rem" }}>
                  {processedUrl ? (
                    <img src={processedUrl} alt="Processed" className="rounded-lg w-full object-contain max-h-72" />
                  ) : (
                    <div className="text-slate-300 text-sm">Processing&hellip;</div>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-2 text-center">
                  {spec.width_mm}&times;{spec.height_mm}mm &middot; {spec.bg_color[0] === 255 && spec.bg_color[1] === 255 && spec.bg_color[2] === 255 ? "White" : "Light grey"} BG &middot; 300 DPI
                </p>
              </div>
            </div>

            {/* Enhancement summary pills */}
            <div className="flex flex-wrap items-center justify-center gap-2 mb-5">
              {[
                { icon: Sun,       text: "Lighting corrected" },
                { icon: Palette,   text: "Background replaced" },
                { icon: Sparkles,  text: "Skin enhanced" },
                { icon: Eye,       text: "Pose straightened" },
                { icon: Crop,      text: "Cropped to spec" },
              ].map((pill) => (
                <div
                  key={pill.text}
                  className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 border border-teal-200/50 px-2.5 py-1 text-xs font-medium text-teal-700"
                >
                  <pill.icon className="h-3 w-3" />
                  {pill.text}
                </div>
              ))}
            </div>

            {/* Compliance checks */}
            {checks.length > 0 && (
              <div className="glass rounded-xl p-5 shadow-glass mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-navy-600 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-teal-500" />
                    Compliance Checks
                  </h3>
                  <span className={cn(
                    "text-xs font-bold rounded-full px-2.5 py-0.5",
                    allPassed
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-amber-100 text-amber-700"
                  )}>
                    {passedCount}/{checks.length} passed
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
                  {checks.map((c, i) => (
                    <motion.div
                      key={c.check || i}
                      initial={{ opacity: 0, x: -5 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="flex items-start gap-2 py-1"
                    >
                      {c.passed ? (
                        <Check className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      ) : (
                        <X className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                      )}
                      <div>
                        <span className="text-sm font-semibold text-navy-600">{c.check}</span>
                        <p className="text-xs text-slate-500">{c.message}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Success/warning banner */}
            {checks.length > 0 && (
              allPassed ? (
                <div className="rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/60 p-4 text-center mb-6">
                  <p className="text-sm font-bold text-emerald-800">
                    All compliance checks passed! Your photo is ready.
                  </p>
                </div>
              ) : (
                <div className="rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/60 p-4 text-center mb-6">
                  <p className="text-sm font-bold text-amber-800">
                    Some checks did not pass. The photo may still be usable, but consider retaking.
                  </p>
                </div>
              )
            )}

            {/* Privacy note */}
            <p className="text-center text-xs text-slate-400 mb-4">
              Your photo is processed securely on our servers and never stored.
            </p>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => processedUrl && sheetUrl && onNext(processedUrl, sheetUrl)}
              disabled={!processedUrl || !sheetUrl}
              className={cn(
                "w-full sm:w-auto mx-auto flex items-center justify-center gap-2 rounded-lg px-8 py-3 text-sm font-bold shadow-lg transition-shadow",
                processedUrl && sheetUrl
                  ? "bg-gradient-to-r from-navy-600 to-navy-500 text-white hover:shadow-xl"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
              )}
            >
              Continue to Download <ArrowRight className="h-4 w-4" />
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
