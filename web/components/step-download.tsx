"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft, Download, FileImage, Printer, Check, Lock,
  CreditCard, Sparkles, Mail, Loader2, Sliders,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type CountrySpec, getSpec } from "@/lib/countries";
import { type ProcessedBundle } from "@/components/step-preview";
import PhotoEditor, {
  type Edits,
  type Variant,
  editsToCssFilter,
  bakeEditsToDataUrl,
  buildPrintSheet,
} from "@/components/photo-editor";

const DOWNLOAD_DPI = 350;
const PREVIEW_DPI = 600;

interface Props {
  country: CountrySpec;
  docType: "passport" | "visa";
  bundle: ProcessedBundle;
  variant: Variant;
  onVariantChange: (v: Variant) => void;
  edits: Edits;
  onEditsChange: (e: Edits) => void;
  editedOverrideUrl: string | null;
  onEditedOverrideChange: (url: string | null) => void;
  onBack: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StepDownload({
  country, docType, bundle,
  variant, onVariantChange, edits, onEditsChange,
  editedOverrideUrl, onEditedOverrideChange,
  onBack,
}: Props) {
  const spec = getSpec(country, docType);
  const [format, setFormat] = useState<"jpeg" | "png">("jpeg");
  const [layout, setLayout] = useState<"single" | "sheet">("single");
  const [paid, setPaid] = useState(false);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // When advanced-tool edits are applied, regenerate the print sheet on
  // the client from the edited photo so the sheet download reflects the
  // same edits. Cache a preview-resolution + download-resolution pair.
  const [editedSheetPreviewUrl, setEditedSheetPreviewUrl] = useState<string | null>(null);
  const [editedSheetDownloadUrl, setEditedSheetDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!editedOverrideUrl) {
      setEditedSheetPreviewUrl(null);
      setEditedSheetDownloadUrl(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [preview, download] = await Promise.all([
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, PREVIEW_DPI),
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, DOWNLOAD_DPI),
        ]);
        if (!cancelled) {
          setEditedSheetPreviewUrl(preview);
          setEditedSheetDownloadUrl(download);
        }
      } catch {
        // Fall back to server-generated sheet on failure.
      }
    })();
    return () => { cancelled = true; };
  }, [editedOverrideUrl, spec.width_mm, spec.height_mm]);

  // Resolve which URL to use for display vs download based on variant,
  // layout, and whether advanced-tool edits are active. Override always
  // wins when present — including the sheet layout, by using the
  // client-regenerated sheet.
  const { displayUrl, downloadUrl } = useMemo(() => {
    if (editedOverrideUrl) {
      if (layout === "single") {
        return { displayUrl: editedOverrideUrl, downloadUrl: editedOverrideUrl };
      }
      // Sheet layout with edits: use regenerated sheet if ready, else
      // briefly fall back to the server sheet while it builds.
      return {
        displayUrl: editedSheetPreviewUrl ?? bundle.previewSheetUrl,
        downloadUrl: editedSheetDownloadUrl ?? bundle.sheetUrl,
      };
    }
    if (variant === "enhanced") {
      return {
        displayUrl: layout === "sheet" ? bundle.previewSheetUrl : bundle.previewUrl,
        downloadUrl: layout === "sheet" ? bundle.sheetUrl : bundle.processedUrl,
      };
    }
    return {
      displayUrl:
        layout === "sheet" ? bundle.originalPreviewSheetUrl : bundle.originalPreviewUrl,
      downloadUrl:
        layout === "sheet" ? bundle.originalSheetUrl : bundle.originalProcessedUrl,
    };
  }, [bundle, variant, layout, editedOverrideUrl, editedSheetPreviewUrl, editedSheetDownloadUrl]);

  const cssFilter = useMemo(() => editsToCssFilter(edits), [edits]);

  // Stripe return flow
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (sessionId && params.get("paid") === "true") {
      fetch(`${API_URL}/api/verify-payment?session_id=${sessionId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.paid) {
            setPaid(true);
            window.history.replaceState({}, "", window.location.pathname);
          }
        })
        .catch(() => setPaid(true));
    }
  }, []);

  const handlePayment = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/create-checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          success_url: window.location.origin + "?paid=true",
          cancel_url: window.location.origin + "?cancelled=true",
        }),
      });
      if (!res.ok) throw new Error("Failed to create checkout session");
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      setPaid(true); // dev fallback
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownload = useCallback(async () => {
    setDownloading(true);
    try {
      // Bake the slider edits into the downloaded file so it matches
      // what the user sees on screen. Skip baking if no edits applied
      // (saves one canvas round-trip + preserves DPI metadata).
      const noEdits =
        edits.brightness === 1 &&
        edits.contrast === 1 &&
        edits.saturation === 1 &&
        edits.warmth === 0;
      const finalUrl = noEdits
        ? downloadUrl
        : await bakeEditsToDataUrl(downloadUrl, edits, format);

      const link = document.createElement("a");
      link.href = finalUrl;
      const base = layout === "sheet" ? "passport_photo_sheet" : "passport_photo";
      link.download = `${base}_${country.name.toLowerCase().replace(/\s+/g, "_")}.${format}`;
      link.click();
    } finally {
      setDownloading(false);
    }
  }, [downloadUrl, edits, format, layout, country]);

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
        <ArrowLeft className="h-4 w-4" /> Back to Preview
      </button>

      {/* Country badge */}
      <div className="inline-flex items-center gap-2 rounded-full bg-navy-600/5 border border-navy-600/10 px-3 py-1 text-sm font-semibold text-navy-600 mb-6">
        <span className="text-base">{country.flag}</span>
        {country.name} &mdash; {docType.charAt(0).toUpperCase() + docType.slice(1)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Preview + format/layout */}
        <div className="lg:col-span-3 space-y-5">
          <div className="glass rounded-xl p-6 shadow-glass">
            <div className="flex flex-col items-center">
              <div className="rounded-lg overflow-hidden bg-white shadow-md border border-slate-100 inline-block">
                <img
                  src={displayUrl}
                  alt="Final photo"
                  className="max-h-80 object-contain"
                  style={{ filter: cssFilter }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-3">
                {layout === "sheet" ? (
                  <>4&times;6&quot; print sheet &middot; 6 photos &middot; 350 DPI print &middot; {format.toUpperCase()}</>
                ) : (
                  <>{spec.width_mm}&times;{spec.height_mm}mm &middot; 350 DPI print &middot; {format.toUpperCase()} &middot; {variant === "enhanced" ? "AI-enhanced" : "Original"}</>
                )}
              </p>
            </div>
          </div>

          {/* Format & layout */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">
                Format
              </label>
              <div className="flex gap-2">
                {(["jpeg", "png"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFormat(f)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2.5 text-sm font-semibold uppercase transition-all",
                      format === f
                        ? "border-teal-400 bg-teal-50 text-teal-700 ring-2 ring-teal-400/20"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                    )}
                  >
                    <FileImage className="h-3.5 w-3.5" />
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">
                Layout
              </label>
              <div className="flex gap-2">
                {([
                  { value: "single" as const, label: "Single", icon: FileImage },
                  { value: "sheet" as const, label: "4\u00d76\"", icon: Printer },
                ]).map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setLayout(value)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2.5 text-sm font-semibold transition-all",
                      layout === value
                        ? "border-teal-400 bg-teal-50 text-teal-700 ring-2 ring-teal-400/20"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Editor */}
          <div className="glass rounded-xl p-5 shadow-glass">
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="h-4 w-4 text-teal-600" />
              <h3 className="text-sm font-bold text-navy-600">Customize your photo</h3>
            </div>
            <PhotoEditor
              variant={variant}
              onVariantChange={onVariantChange}
              edits={edits}
              onEditsChange={onEditsChange}
              previewUrl={displayUrl}
              advancedSrcUrl={bundle.previewUrl}
              bgColor={spec.bg_color as [number, number, number]}
              onAdvancedApply={(url) => onEditedOverrideChange(url)}
              compact
            />
          </div>
        </div>

        {/* Right: Payment / Download */}
        <div className="lg:col-span-2">
          {paid ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 p-6 text-center"
            >
              <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100">
                <Sparkles className="h-7 w-7 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-emerald-800 mb-1">
                Your Photo is Ready!
              </h3>
              <p className="text-sm text-emerald-700/70 mb-5">
                Your edits will be applied to the downloaded file.
              </p>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleDownload}
                disabled={downloading}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 px-6 py-3 text-sm font-bold text-white shadow-lg mb-3",
                  downloading && "opacity-70 cursor-not-allowed",
                )}
              >
                {downloading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Preparing file&hellip;
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Download {layout === "sheet" ? "Print Sheet" : "Photo"} ({format.toUpperCase()})
                  </>
                )}
              </motion.button>

              <button
                onClick={() => {
                  setLayout(layout === "single" ? "sheet" : "single");
                  setTimeout(handleDownload, 100);
                }}
                className="w-full rounded-lg border border-slate-200 bg-white px-6 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Also download {layout === "single" ? "6-up Print Sheet" : "Single Photo"}
              </button>

              <div className="mt-5 pt-4 border-t border-emerald-200/50">
                <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                  <Mail className="h-3.5 w-3.5" />
                  Email a copy to yourself
                </div>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="you@example.com"
                    className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20"
                  />
                  <button className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 transition-colors">
                    Send
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="glass rounded-xl p-6 shadow-glass-lg border-glow">
              <div className="text-center mb-5">
                <h3 className="text-lg font-bold text-navy-600 mb-1">
                  Unlock Your Download
                </h3>
                <p className="text-sm text-slate-500">
                  One-time payment. No subscription.
                </p>
              </div>

              <div className="text-center mb-5">
                <span className="text-4xl font-extrabold bg-gradient-to-r from-navy-600 to-teal-500 bg-clip-text text-transparent">
                  $4.99
                </span>
                <p className="text-xs text-slate-400 mt-1">USD &middot; Secure Stripe checkout</p>
              </div>

              <div className="space-y-2 mb-6">
                {[
                  "Choose AI-Enhanced or Original version",
                  "Fine-tune brightness, contrast, warmth",
                  "Watermark-free high-resolution photo",
                  "350 DPI print-ready (600 DPI preview)",
                  "JPEG and PNG formats",
                  "6-up print sheet (4\u00d76\") included",
                ].map((f) => (
                  <div key={f} className="flex items-start gap-2 text-sm text-slate-600">
                    <Check className="h-4 w-4 text-teal-500 mt-0.5 flex-shrink-0" />
                    {f}
                  </div>
                ))}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handlePayment}
                disabled={loading}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-navy-600 to-navy-500 px-6 py-3.5 text-sm font-bold text-white shadow-lg hover:shadow-xl transition-shadow",
                  loading && "opacity-70 cursor-not-allowed"
                )}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Redirecting to Stripe...
                  </>
                ) : (
                  <>
                    <CreditCard className="h-4 w-4" />
                    Pay $4.99 &amp; Download
                  </>
                )}
              </motion.button>

              <div className="flex items-center justify-center gap-4 mt-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Lock className="h-3 w-3" /> Secure
                </span>
                <span className="flex items-center gap-1">
                  <CreditCard className="h-3 w-3" /> Stripe
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
