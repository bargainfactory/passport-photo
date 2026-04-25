"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, ArrowRight, ScanFace, Palette, Crop, ShieldCheck,
  Check, X, Loader2, AlertTriangle, RefreshCw, Sun, Sparkles, Eye, RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type CountrySpec, getSpec } from "@/lib/countries";
import PhotoEditor, {
  type Edits,
  type Variant,
  editsToCssFilter,
} from "@/components/photo-editor";

export interface ProcessedBundle {
  processedUrl: string;
  sheetUrl: string;
  previewUrl: string;
  previewSheetUrl: string;
  originalProcessedUrl: string;
  originalSheetUrl: string;
  originalPreviewUrl: string;
  originalPreviewSheetUrl: string;
}

interface Props {
  country: CountrySpec;
  docType: "passport" | "visa";
  imageUrl: string;
  variant: Variant;
  onVariantChange: (v: Variant) => void;
  edits: Edits;
  onEditsChange: (e: Edits) => void;
  editedOverrideUrl: string | null;
  onEditedOverrideChange: (url: string | null) => void;
  onNext: (bundle: ProcessedBundle) => void;
  onBack: () => void;
}

interface ValidationCheck {
  check: string;
  passed: boolean;
  message: string;
}

const STAGES = [
  { icon: ScanFace,    label: "Detecting face & features...",  done: "Face detected"          },
  { icon: Eye,         label: "Correcting pose & alignment...",done: "Pose corrected"          },
  { icon: Sun,         label: "Fixing lighting & shadows...",  done: "Lighting fixed"          },
  { icon: Palette,     label: "Removing background...",        done: "Background removed"      },
  { icon: Sparkles,    label: "Enhancing & retouching...",     done: "Enhanced"                },
  { icon: Crop,        label: "Cropping to exact specs...",    done: "Cropped to spec"         },
  { icon: ShieldCheck, label: "Validating compliance...",      done: "Compliance validated"    },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StepPreview({
  country, docType, imageUrl,
  variant, onVariantChange, edits, onEditsChange,
  editedOverrideUrl, onEditedOverrideChange,
  onNext, onBack,
}: Props) {
  const [stage, setStage] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bundle, setBundle] = useState<ProcessedBundle | null>(null);
  const [checks, setChecks] = useState<ValidationCheck[]>([]);
  const spec = getSpec(country, docType);

  const runProcessing = useCallback(async () => {
    setStage(0);
    setDone(false);
    setError(null);
    setBundle(null);
    setChecks([]);
    onEditedOverrideChange(null);

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
          print_sheet: spec.print_sheet ?? null,
        }),
      });

      clearTimeout(timeoutId);
      stageTimers.forEach(clearTimeout);

      if (!res.ok) {
        let errMsg = `Server error ${res.status}`;
        try { const body = await res.json(); errMsg = body.detail || errMsg; } catch {}
        throw new Error(errMsg);
      }

      let data;
      try { data = await res.json(); } catch { throw new Error("Invalid response from server"); }

      if (!data.processed_b64 || !data.sheet_b64) {
        throw new Error("Server returned incomplete data");
      }

      setBundle({
        processedUrl: data.processed_b64,
        sheetUrl: data.sheet_b64,
        previewUrl: data.preview_b64 || data.processed_b64,
        previewSheetUrl: data.preview_sheet_b64 || data.sheet_b64,
        originalProcessedUrl: data.original_processed_b64 || data.processed_b64,
        originalSheetUrl: data.original_sheet_b64 || data.sheet_b64,
        originalPreviewUrl: data.original_preview_b64 || data.preview_b64 || data.processed_b64,
        originalPreviewSheetUrl: data.original_preview_sheet_b64 || data.preview_sheet_b64 || data.sheet_b64,
      });
      setChecks(Array.isArray(data.validation) ? data.validation : []);
      setStage(STAGES.length);
      setTimeout(() => setDone(true), 400);
    } catch (err: unknown) {
      stageTimers.forEach(clearTimeout);
      let msg = "Processing failed. Please try again.";
      if (err instanceof Error) {
        if (err.name === "AbortError") msg = "Processing timed out. Try with a smaller or clearer photo.";
        else if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError"))
          msg = "Cannot reach the processing server. Make sure the backend is running on port 8000.";
        else msg = err.message;
      }
      setError(msg);
    }
  }, [imageUrl, spec, onEditedOverrideChange]);

  useEffect(() => { runProcessing(); }, [runProcessing]);

  const passedCount = checks.filter((c) => c.passed).length;
  const allPassed = checks.length > 0 && checks.every((c) => c.passed);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-accent-300 transition-colors mb-3"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <div className="inline-flex items-center gap-2 rounded-full bg-accent-50 border border-[rgba(0,212,255,0.1)] px-3 py-1 text-sm font-semibold text-accent-300 mb-4">
        <span className="text-base">{country.flag}</span>
        {country.name} &mdash; {docType.charAt(0).toUpperCase() + docType.slice(1)}
      </div>

      <AnimatePresence mode="wait">
        {error ? (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass rounded-xl p-8 text-center max-w-lg mx-auto"
          >
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="h-7 w-7 text-red-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Processing Error</h3>
            <p className="text-sm text-slate-400 mb-5 max-w-sm mx-auto">{error}</p>
            <div className="flex items-center justify-center gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={runProcessing}
                className="btn-glow flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-bold text-white"
              >
                <RefreshCw className="h-4 w-4" /> Retry
              </motion.button>
              <button
                onClick={onBack}
                className="btn-ghost rounded-lg px-5 py-2.5 text-sm font-medium text-slate-300"
              >
                Upload Different Photo
              </button>
            </div>
          </motion.div>
        ) : !done ? (
          /* Processing animation */
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass rounded-xl p-6 max-w-xl mx-auto"
          >
            <div className="relative mx-auto mb-6 h-32 w-32">
              <motion.div
                animate={{ scale: [1, 1.1, 1], opacity: [0.2, 0.4, 0.2] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-[-8px] rounded-2xl bg-gradient-to-br from-accent-300/40 to-accent-500/30 blur-sm"
              />
              <div className="relative h-full w-full rounded-2xl overflow-hidden border border-accent-300/20 shadow-glow-teal">
                <img src={imageUrl} alt="" className="h-full w-full object-cover" />
                <div className="absolute inset-0 bg-deep/40 flex items-center justify-center backdrop-blur-[2px]">
                  <Loader2 className="h-10 w-10 text-accent-300 animate-spin drop-shadow-lg" />
                </div>
              </div>
            </div>

            <h3 className="text-center text-base font-bold text-white mb-1">
              AI Processing Your Photo
            </h3>
            <p className="text-center text-xs text-slate-500 mb-5">
              Transforming your selfie into a professional passport photo
            </p>

            <div className="space-y-2 max-w-sm mx-auto">
              {STAGES.map((s, i) => {
                const Icon = s.icon;
                const isComplete = i < stage;
                const isCurrent = i === stage;
                return (
                  <motion.div
                    key={s.label}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="flex items-center gap-3"
                  >
                    <div className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-lg transition-all duration-500",
                      isComplete && "bg-accent-300/15 text-accent-300",
                      isCurrent && "bg-accent-300/10 text-accent-300 shadow-glow-sm",
                      !isComplete && !isCurrent && "bg-deep-200 text-slate-600"
                    )}>
                      {isComplete ? (
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 500, damping: 15 }}>
                          <Check className="h-3.5 w-3.5" />
                        </motion.div>
                      ) : isCurrent ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Icon className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <span className={cn(
                      "text-xs font-medium transition-colors duration-500",
                      isComplete && "text-accent-300",
                      isCurrent && "text-white",
                      !isComplete && !isCurrent && "text-slate-600"
                    )}>
                      {isComplete ? s.done : s.label}
                    </span>
                  </motion.div>
                );
              })}
            </div>

            {/* Progress bar with wave effect */}
            <div className="mt-5 h-1.5 w-full rounded-full bg-deep-200 overflow-hidden wave-bar">
              <motion.div
                initial={{ width: "0%" }}
                animate={{ width: `${Math.min((stage / STAGES.length) * 100, 95)}%` }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
                className="h-full rounded-full bg-gradient-to-r from-accent-300 via-accent-400 to-accent-500"
                style={{ boxShadow: "0 0 12px rgba(0, 212, 255, 0.5)" }}
              />
            </div>

            <p className="text-[11px] text-slate-600 mt-3 text-center">
              AI is enhancing your photo. This may take 15&ndash;30 seconds&hellip;
            </p>
          </motion.div>
        ) : (
          /* Results */
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Before / After */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
              <div className="glass rounded-xl p-4">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Original</p>
                <div className="rounded-lg overflow-hidden bg-deep-200 flex items-center justify-center" style={{ minHeight: "10rem" }}>
                  <img src={imageUrl} alt="Original" className="rounded-lg w-full object-contain max-h-64" />
                </div>
              </div>

              <div className="rounded-xl p-4 border border-accent-300/20 bg-gradient-to-br from-deep-100 to-deep-50 glow-border-active">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] font-bold text-accent-300 uppercase tracking-wider">
                    {variant === "enhanced" ? "AI Enhanced" : "Cropped Only"}
                  </p>
                  {variant === "enhanced" && (
                    <span className="flex items-center gap-1 rounded-full bg-accent-300/10 border border-accent-300/15 px-2 py-0.5 text-[10px] font-semibold text-accent-300">
                      <Sparkles className="h-2.5 w-2.5" /> Studio Quality
                    </span>
                  )}
                </div>
                <div className="rounded-lg overflow-hidden bg-deep-200 flex items-center justify-center" style={{ minHeight: "10rem" }}>
                  {bundle ? (
                    <img
                      src={editedOverrideUrl ?? (variant === "enhanced" ? bundle.previewUrl : bundle.originalPreviewUrl)}
                      alt="Processed"
                      className="rounded-lg w-full object-contain max-h-64"
                      style={{ filter: editsToCssFilter(edits) }}
                    />
                  ) : (
                    <div className="text-slate-600 text-sm">Processing&hellip;</div>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-2 text-center">
                  {spec.width_mm}&times;{spec.height_mm}mm &middot; {spec.bg_color[0] === 255 && spec.bg_color[1] === 255 && spec.bg_color[2] === 255 ? "White" : "Light grey"} BG &middot; 350 DPI
                </p>
              </div>
            </div>

            {/* Variant toggle */}
            <div className="flex items-center justify-center gap-2 mb-4">
              <button
                type="button"
                onClick={() => { onVariantChange("enhanced"); onEditedOverrideChange(null); }}
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-4 py-2.5 text-xs font-semibold transition-all",
                  variant === "enhanced"
                    ? "border-accent-300/30 bg-accent-50 text-accent-300 shadow-glow-sm"
                    : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]",
                )}
              >
                <Sparkles className="h-3.5 w-3.5" /> AI Enhanced
              </button>
              <button
                type="button"
                onClick={() => { onVariantChange("original"); onEditedOverrideChange(null); }}
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-4 py-2.5 text-xs font-semibold transition-all",
                  variant === "original"
                    ? "border-accent-300/30 bg-accent-50 text-accent-300 shadow-glow-sm"
                    : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]",
                )}
              >
                <Crop className="h-3.5 w-3.5" /> Cropped Only
              </button>
            </div>

            {/* Enhancement pills */}
            <div className={cn("flex flex-wrap items-center justify-center gap-2 mb-4", variant === "original" && "opacity-40")}>
              {[
                { icon: Sun, text: "Lighting corrected" },
                { icon: Palette, text: "Background replaced" },
                { icon: Sparkles, text: "Skin enhanced" },
                { icon: Eye, text: "Pose straightened" },
                { icon: Crop, text: "Cropped to spec" },
              ].map((pill) => (
                <div
                  key={pill.text}
                  className="inline-flex items-center gap-1.5 rounded-full bg-accent-50 border border-[rgba(0,212,255,0.08)] px-2.5 py-1 text-[11px] font-medium text-accent-300"
                >
                  <pill.icon className="h-3 w-3" />
                  {pill.text}
                </div>
              ))}
            </div>

            {/* Compliance + Customize */}
            {(checks.length > 0 || bundle) && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
                {checks.length > 0 && (
                  <div className="glass rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2.5">
                      <h3 className="text-xs font-bold text-white flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4 text-accent-300" />
                        Compliance
                      </h3>
                      <span className={cn(
                        "text-[10px] font-bold rounded-full px-2 py-0.5",
                        allPassed
                          ? "bg-accent-300/10 text-accent-300 border border-accent-300/15"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/15"
                      )}>
                        {passedCount}/{checks.length}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-0.5">
                      {checks.map((c, i) => (
                        <motion.div
                          key={c.check || i}
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-start gap-2 py-1"
                        >
                          {c.passed ? (
                            <Check className="h-3.5 w-3.5 text-accent-300 mt-0.5 flex-shrink-0" />
                          ) : (
                            <X className="h-3.5 w-3.5 text-red-400 mt-0.5 flex-shrink-0" />
                          )}
                          <div>
                            <span className="text-xs font-semibold text-white/80">{c.check}</span>
                            <p className="text-[11px] text-slate-500">{c.message}</p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {bundle && (
                  <div className="glass rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2.5">
                      <Sparkles className="h-4 w-4 text-accent-300" />
                      <h3 className="text-xs font-bold text-white">Customize</h3>
                    </div>
                    <PhotoEditor
                      variant={variant}
                      onVariantChange={onVariantChange}
                      edits={edits}
                      onEditsChange={onEditsChange}
                      previewUrl={
                        editedOverrideUrl ?? (variant === "enhanced" ? bundle.previewUrl : bundle.originalPreviewUrl)
                      }
                      advancedSrcUrl={variant === "enhanced" ? bundle.previewUrl : bundle.originalPreviewUrl}
                      bgColor={spec.bg_color as [number, number, number]}
                      onAdvancedApply={(url) => onEditedOverrideChange(url)}
                      compact
                    />
                  </div>
                )}
              </div>
            )}

            {/* Banner */}
            {checks.length > 0 && (
              allPassed ? (
                <div className="rounded-xl bg-accent-300/5 border border-accent-300/15 p-3 text-center mb-4">
                  <p className="text-xs font-bold text-accent-300">
                    All compliance checks passed! Your photo is ready.
                  </p>
                </div>
              ) : (
                <div className="rounded-xl bg-amber-500/5 border border-amber-500/15 p-3 text-center mb-4">
                  <p className="text-xs font-bold text-amber-400">
                    Some checks did not pass. The photo may still be usable.
                  </p>
                </div>
              )
            )}

            <p className="text-center text-[11px] text-slate-600 mb-3">
              Your photo is processed securely and never stored.
            </p>

            <div className="flex flex-col items-center gap-2.5">
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => bundle && onNext(bundle)}
                disabled={!bundle}
                className={cn(
                  "w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl px-8 py-3 text-sm font-bold transition-all",
                  bundle ? "btn-glow text-white" : "bg-deep-200 text-slate-600 cursor-not-allowed"
                )}
              >
                Continue to Download <ArrowRight className="h-4 w-4" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onBack}
                className="btn-ghost inline-flex items-center gap-2 rounded-lg px-6 py-2.5 text-sm font-semibold text-slate-300"
              >
                <RotateCcw className="h-4 w-4" /> Retake
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
