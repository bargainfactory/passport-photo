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
  fitJpegUnderKB,
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

  // Pre-payment: which products the user wants to buy.
  const [selection, setSelection] = useState<{ digital: boolean; sheet: boolean }>({
    digital: true,
    sheet: false,
  });

  // Post-payment: what the user actually owns. null = not purchased yet.
  const [purchased, setPurchased] = useState<{ digital: boolean; sheet: boolean } | null>(null);

  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<"digital" | "sheet" | null>(null);

  const priceCents = useMemo(() => {
    if (selection.digital && selection.sheet) return 799;
    if (selection.digital || selection.sheet) return 499;
    return 0;
  }, [selection]);
  const priceStr = `$${(priceCents / 100).toFixed(2)}`;

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
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, PREVIEW_DPI, "jpeg", spec.print_sheet),
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, DOWNLOAD_DPI, "jpeg", spec.print_sheet),
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
  }, [editedOverrideUrl, spec.width_mm, spec.height_mm, spec.print_sheet]);

  // Resolve source URL for a given product kind at either display or
  // download resolution. Edited overrides win over stock variants; the
  // sheet has a client-regenerated fallback when edits are present.
  const resolveUrl = useCallback(
    (kind: "digital" | "sheet", res: "display" | "download"): string => {
      if (editedOverrideUrl) {
        if (kind === "digital") return editedOverrideUrl;
        return res === "display"
          ? (editedSheetPreviewUrl ?? bundle.previewSheetUrl)
          : (editedSheetDownloadUrl ?? bundle.sheetUrl);
      }
      if (kind === "digital") {
        return variant === "enhanced"
          ? (res === "display" ? bundle.previewUrl : bundle.processedUrl)
          : (res === "display" ? bundle.originalPreviewUrl : bundle.originalProcessedUrl);
      }
      return variant === "enhanced"
        ? (res === "display" ? bundle.previewSheetUrl : bundle.sheetUrl)
        : (res === "display" ? bundle.originalPreviewSheetUrl : bundle.originalSheetUrl);
    },
    [bundle, variant, editedOverrideUrl, editedSheetPreviewUrl, editedSheetDownloadUrl],
  );

  const displayUrl = useMemo(
    () => resolveUrl(layout === "single" ? "digital" : "sheet", "display"),
    [resolveUrl, layout],
  );

  const cssFilter = useMemo(() => editsToCssFilter(edits), [edits]);

  // Stripe return flow — read the purchased items from the session
  // metadata so we only unlock what the user actually paid for.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (sessionId && params.get("paid") === "true") {
      fetch(`${API_URL}/api/verify-payment?session_id=${sessionId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.paid) {
            const items: string[] = data.items || [];
            setPurchased({
              digital: items.includes("digital"),
              sheet: items.includes("sheet"),
            });
            window.history.replaceState({}, "", window.location.pathname);
          }
        })
        .catch(() => {
          // Dev fallback when Stripe isn't configured: grant whatever
          // was selected before the redirect attempt.
          setPurchased({ digital: selection.digital, sheet: selection.sheet });
        });
    }
    // `selection` intentionally not in deps — we only want the fallback
    // to read its value once, on return from Stripe.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If the user bought only one product, snap the preview to it.
  useEffect(() => {
    if (!purchased) return;
    if (purchased.digital && !purchased.sheet) setLayout("single");
    else if (!purchased.digital && purchased.sheet) setLayout("sheet");
  }, [purchased]);

  const handlePayment = useCallback(async () => {
    if (priceCents === 0) return;
    setLoading(true);
    try {
      const items: string[] = [];
      if (selection.digital) items.push("digital");
      if (selection.sheet) items.push("sheet");

      const res = await fetch(`${API_URL}/api/create-checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items,
          success_url: window.location.origin + "?paid=true",
          cancel_url: window.location.origin + "?cancelled=true",
        }),
      });
      if (!res.ok) throw new Error("Failed to create checkout session");
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      // Dev fallback — grant selected items locally.
      setPurchased({ digital: selection.digital, sheet: selection.sheet });
    } finally {
      setLoading(false);
    }
  }, [selection, priceCents]);

  const handleDownload = useCallback(async (kind: "digital" | "sheet") => {
    setDownloading(kind);
    try {
      const sourceUrl = resolveUrl(kind, "download");

      // Bake the slider edits into the downloaded file so it matches
      // what the user sees on screen. Skip baking if no edits applied
      // (saves one canvas round-trip + preserves DPI metadata).
      const noEdits =
        edits.brightness === 1 &&
        edits.contrast === 1 &&
        edits.saturation === 1 &&
        edits.warmth === 0;
      let finalUrl = noEdits
        ? sourceUrl
        : await bakeEditsToDataUrl(sourceUrl, edits, format);

      // Enforce per-country file-size cap on the digital JPEG only
      // (e.g. US passport = 230 KB). Print sheets are meant for home
      // printing, not online submission, so they're untouched.
      if (kind === "digital" && format === "jpeg" && spec.max_file_size_kb) {
        finalUrl = await fitJpegUnderKB(finalUrl, spec.max_file_size_kb);
      }

      const link = document.createElement("a");
      link.href = finalUrl;
      const base = kind === "sheet" ? "passport_photo_sheet" : "passport_photo";
      link.download = `${base}_${country.name.toLowerCase().replace(/\s+/g, "_")}.${format}`;
      link.click();
    } finally {
      setDownloading(null);
    }
  }, [resolveUrl, edits, format, country, spec.max_file_size_kb]);

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
                Preview
              </label>
              <div className="flex gap-2">
                {([
                  { value: "single" as const, label: "Digital Download", icon: FileImage },
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
          {purchased ? (
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

              <div className="space-y-2.5">
                {purchased.digital && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleDownload("digital")}
                    disabled={downloading !== null}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 px-6 py-3 text-sm font-bold text-white shadow-lg",
                      downloading !== null && "opacity-70 cursor-not-allowed",
                    )}
                  >
                    {downloading === "digital" ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Preparing file&hellip;</>
                    ) : (
                      <><Download className="h-4 w-4" /> Download Digital ({format.toUpperCase()})</>
                    )}
                  </motion.button>
                )}
                {purchased.sheet && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleDownload("sheet")}
                    disabled={downloading !== null}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-lg border-2 border-emerald-500 bg-white px-6 py-3 text-sm font-bold text-emerald-700 shadow-md",
                      downloading !== null && "opacity-70 cursor-not-allowed",
                    )}
                  >
                    {downloading === "sheet" ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Preparing file&hellip;</>
                    ) : (
                      <><Printer className="h-4 w-4" /> Download 4&times;6&quot; Print Sheet ({format.toUpperCase()})</>
                    )}
                  </motion.button>
                )}
              </div>

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
                  Choose Your Package
                </h3>
                <p className="text-sm text-slate-500">
                  Pick one or both. One-time payment.
                </p>
              </div>

              <div className="space-y-2.5 mb-5">
                <button
                  type="button"
                  onClick={() => setSelection((s) => ({ ...s, digital: !s.digital }))}
                  className={cn(
                    "w-full flex items-center gap-3 rounded-lg border p-3 text-left transition-all",
                    selection.digital
                      ? "border-teal-400 bg-teal-50 ring-2 ring-teal-400/20"
                      : "border-slate-200 bg-white hover:border-slate-300",
                  )}
                >
                  <div
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded border flex-shrink-0",
                      selection.digital ? "bg-teal-500 border-teal-500" : "border-slate-300 bg-white",
                    )}
                  >
                    {selection.digital && <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-navy-600">Digital Download</span>
                      <span className="text-sm font-bold text-teal-600">$4.99</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {spec.width_mm}&times;{spec.height_mm}mm JPEG
                      {spec.max_file_size_kb ? ` · \u2264${spec.max_file_size_kb} KB` : ""}
                      {" · for online submission"}
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setSelection((s) => ({ ...s, sheet: !s.sheet }))}
                  className={cn(
                    "w-full flex items-center gap-3 rounded-lg border p-3 text-left transition-all",
                    selection.sheet
                      ? "border-teal-400 bg-teal-50 ring-2 ring-teal-400/20"
                      : "border-slate-200 bg-white hover:border-slate-300",
                  )}
                >
                  <div
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded border flex-shrink-0",
                      selection.sheet ? "bg-teal-500 border-teal-500" : "border-slate-300 bg-white",
                    )}
                  >
                    {selection.sheet && <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-navy-600">4&times;6&quot; Print Sheet</span>
                      <span className="text-sm font-bold text-teal-600">$4.99</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      6 photos on one sheet &middot; for home or photo-lab printing
                    </p>
                  </div>
                </button>

                {selection.digital && selection.sheet && (
                  <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-xs font-semibold text-emerald-700 text-center">
                    Bundle &mdash; save $2.00
                  </div>
                )}
              </div>

              <div className="text-center mb-5">
                <span className="text-4xl font-extrabold bg-gradient-to-r from-navy-600 to-teal-500 bg-clip-text text-transparent">
                  {priceStr}
                </span>
                <p className="text-xs text-slate-400 mt-1">USD &middot; Secure Stripe checkout</p>
              </div>

              <motion.button
                whileHover={{ scale: priceCents > 0 ? 1.02 : 1 }}
                whileTap={{ scale: priceCents > 0 ? 0.98 : 1 }}
                onClick={handlePayment}
                disabled={loading || priceCents === 0}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-navy-600 to-navy-500 px-6 py-3.5 text-sm font-bold text-white shadow-lg hover:shadow-xl transition-shadow",
                  (loading || priceCents === 0) && "opacity-60 cursor-not-allowed"
                )}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Redirecting to Stripe...
                  </>
                ) : priceCents === 0 ? (
                  <>
                    <CreditCard className="h-4 w-4" />
                    Select at least one item
                  </>
                ) : (
                  <>
                    <CreditCard className="h-4 w-4" />
                    Pay {priceStr} &amp; Download
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
