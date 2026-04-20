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
  type Tier = "digital" | "sheet" | "bundle";
  const [selectedTier, setSelectedTier] = useState<Tier>("digital");
  const [purchased, setPurchased] = useState<{ digital: boolean; sheet: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<"digital" | "sheet" | null>(null);

  const selection = useMemo(() => ({
    digital: selectedTier === "digital" || selectedTier === "bundle",
    sheet: selectedTier === "sheet" || selectedTier === "bundle",
  }), [selectedTier]);

  const priceCents = useMemo(() => {
    if (selectedTier === "bundle") return 899;
    return 499;
  }, [selectedTier]);
  const priceStr = `$${(priceCents / 100).toFixed(2)}`;

  const [editedSheetPreviewUrl, setEditedSheetPreviewUrl] = useState<string | null>(null);
  const [editedSheetDownloadUrl, setEditedSheetDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!editedOverrideUrl) { setEditedSheetPreviewUrl(null); setEditedSheetDownloadUrl(null); return; }
    let cancelled = false;
    (async () => {
      try {
        const [preview, download] = await Promise.all([
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, PREVIEW_DPI, "jpeg", spec.print_sheet),
          buildPrintSheet(editedOverrideUrl, spec.width_mm, spec.height_mm, DOWNLOAD_DPI, "jpeg", spec.print_sheet),
        ]);
        if (!cancelled) { setEditedSheetPreviewUrl(preview); setEditedSheetDownloadUrl(download); }
      } catch {}
    })();
    return () => { cancelled = true; };
  }, [editedOverrideUrl, spec.width_mm, spec.height_mm, spec.print_sheet]);

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

  const displayUrl = useMemo(() => resolveUrl(layout === "single" ? "digital" : "sheet", "display"), [resolveUrl, layout]);
  const cssFilter = useMemo(() => editsToCssFilter(edits), [edits]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (sessionId && params.get("paid") === "true") {
      fetch(`${API_URL}/api/verify-payment?session_id=${sessionId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.paid) {
            const items: string[] = data.items || [];
            setPurchased({ digital: items.includes("digital"), sheet: items.includes("sheet") });
            window.history.replaceState({}, "", window.location.pathname);
          }
        })
        .catch(() => { setPurchased({ digital: selection.digital, sheet: selection.sheet }); });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!purchased) return;
    if (purchased.digital && !purchased.sheet) setLayout("single");
    else if (!purchased.digital && purchased.sheet) setLayout("sheet");
  }, [purchased]);

  const handlePayment = useCallback(async () => {
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
      setPurchased({ digital: selection.digital, sheet: selection.sheet });
    } finally { setLoading(false); }
  }, [selection, priceCents]);

  const handleDownload = useCallback(async (kind: "digital" | "sheet") => {
    setDownloading(kind);
    try {
      const sourceUrl = resolveUrl(kind, "download");
      const noEdits = edits.brightness === 1 && edits.contrast === 1 && edits.saturation === 1 && edits.warmth === 0;
      let finalUrl = noEdits ? sourceUrl : await bakeEditsToDataUrl(sourceUrl, edits, format);
      if (kind === "digital" && format === "jpeg" && spec.max_file_size_kb) {
        finalUrl = await fitJpegUnderKB(finalUrl, spec.max_file_size_kb);
      }
      const link = document.createElement("a");
      link.href = finalUrl;
      link.download = `${kind === "sheet" ? "passport_photo_sheet" : "passport_photo"}_${country.name.toLowerCase().replace(/\s+/g, "_")}.${format}`;
      link.click();
    } finally { setDownloading(null); }
  }, [resolveUrl, edits, format, country, spec.max_file_size_kb]);

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

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: Preview + format/layout */}
        <div className="lg:col-span-3 space-y-4">
          <div className="glass rounded-xl p-5">
            <div className="flex flex-col items-center">
              <div className="rounded-lg overflow-hidden bg-deep-200 shadow-glow-sm border border-[rgba(0,212,255,0.1)] inline-block">
                <img src={displayUrl} alt="Final photo" className="max-h-72 object-contain" style={{ filter: cssFilter }} />
              </div>
              <p className="text-[11px] text-slate-500 mt-2.5">
                {layout === "sheet" ? (
                  <>4&times;6&quot; print sheet &middot; 6 photos &middot; 350 DPI &middot; {format.toUpperCase()}</>
                ) : (
                  <>{spec.width_mm}&times;{spec.height_mm}mm &middot; 350 DPI &middot; {format.toUpperCase()} &middot; {variant === "enhanced" ? "AI-enhanced" : "Original"}</>
                )}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">Format</label>
              <div className="flex gap-2">
                {(["jpeg", "png"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFormat(f)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold uppercase transition-all",
                      format === f
                        ? "border-accent-300/30 bg-accent-50 text-accent-300"
                        : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]"
                    )}
                  >
                    <FileImage className="h-3 w-3" /> {f}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">Preview</label>
              <div className="flex gap-2">
                {([
                  { value: "single" as const, label: "Digital", icon: FileImage },
                  { value: "sheet" as const, label: "4\u00d76\"", icon: Printer },
                ]).map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setLayout(value)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all",
                      layout === value
                        ? "border-accent-300/30 bg-accent-50 text-accent-300"
                        : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]"
                    )}
                  >
                    <Icon className="h-3 w-3" /> {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sliders className="h-4 w-4 text-accent-300" />
              <h3 className="text-xs font-bold text-white">Customize</h3>
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
              className="rounded-xl bg-gradient-to-br from-accent-300/5 to-accent-500/5 border border-accent-300/15 p-5 text-center"
            >
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-300/10 border border-accent-300/15">
                <Sparkles className="h-6 w-6 text-accent-300" />
              </div>
              <h3 className="text-lg font-bold text-white mb-1">Your Photo is Ready!</h3>
              <p className="text-xs text-slate-400 mb-4">Edits will be applied to the downloaded file.</p>

              <div className="space-y-2">
                {purchased.digital && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleDownload("digital")}
                    disabled={downloading !== null}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-xl btn-glow px-6 py-3 text-sm font-bold text-white",
                      downloading !== null && "opacity-70 cursor-not-allowed",
                    )}
                  >
                    {downloading === "digital" ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Preparing&hellip;</>
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
                      "w-full flex items-center justify-center gap-2 rounded-xl btn-ghost px-6 py-3 text-sm font-bold text-accent-300",
                      downloading !== null && "opacity-70 cursor-not-allowed",
                    )}
                  >
                    {downloading === "sheet" ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Preparing&hellip;</>
                    ) : (
                      <><Printer className="h-4 w-4" /> Download Print Sheet ({format.toUpperCase()})</>
                    )}
                  </motion.button>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-accent-300/10">
                <div className="flex items-center gap-2 text-[11px] text-slate-500 mb-1.5">
                  <Mail className="h-3 w-3" /> Email a copy
                </div>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="you@example.com"
                    className="flex-1 rounded-lg border border-[rgba(0,212,255,0.1)] bg-deep-100 px-3 py-2 text-xs text-white outline-none focus:border-accent-300/30 focus:ring-1 focus:ring-accent-300/10 placeholder:text-slate-600"
                  />
                  <button className="btn-ghost rounded-lg px-3 py-2 text-xs font-medium text-slate-300">Send</button>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="glass rounded-xl p-5 glow-border-active">
              <div className="text-center mb-4">
                <h3 className="text-base font-bold text-white mb-1">Choose Your Package</h3>
                <p className="text-xs text-slate-500">One-time payment. No subscription.</p>
              </div>

              <div className="space-y-2 mb-4">
                {([
                  {
                    tier: "digital" as Tier,
                    title: "Digital Download",
                    price: "$4.99",
                    desc: `${spec.width_mm}\u00d7${spec.height_mm}mm JPEG${spec.max_file_size_kb ? ` \u00b7 \u2264${spec.max_file_size_kb} KB` : ""} \u00b7 online submission`,
                    icon: FileImage,
                    badge: null,
                  },
                  {
                    tier: "sheet" as Tier,
                    title: "4\u00d76\" Print Sheet",
                    price: "$4.99",
                    desc: "6 photos on one sheet \u00b7 home or lab printing",
                    icon: Printer,
                    badge: null,
                  },
                  {
                    tier: "bundle" as Tier,
                    title: "Bundled Deal",
                    price: "$8.99",
                    desc: "Digital download + 4\u00d76\" print sheet \u00b7 best value",
                    icon: Sparkles,
                    badge: "Save $0.99",
                  },
                ] as const).map(({ tier, title, price, desc, icon: Icon, badge }) => (
                  <button
                    key={tier}
                    type="button"
                    onClick={() => setSelectedTier(tier)}
                    className={cn(
                      "w-full flex items-center gap-3 rounded-lg border p-3 text-left transition-all relative",
                      selectedTier === tier
                        ? tier === "bundle"
                          ? "border-accent-300/40 bg-accent-50 ring-1 ring-accent-300/15"
                          : "border-accent-300/25 bg-accent-50"
                        : "border-[rgba(0,212,255,0.08)] bg-deep-100 hover:border-[rgba(0,212,255,0.15)]",
                    )}
                  >
                    <div className={cn(
                      "flex h-5 w-5 items-center justify-center rounded-full border flex-shrink-0",
                      selectedTier === tier
                        ? "bg-gradient-to-br from-accent-300 to-accent-500 border-accent-300"
                        : "border-slate-600 bg-deep-200",
                    )}>
                      {selectedTier === tier && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-bold text-white flex items-center gap-1.5">
                          <Icon className="h-3.5 w-3.5 text-accent-300/70" />
                          {title}
                        </span>
                        <span className="text-sm font-bold text-accent-300">{price}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">{desc}</p>
                    </div>
                    {badge && (
                      <span className="absolute -top-2 right-3 rounded-full bg-gradient-to-r from-accent-300 to-accent-500 px-2 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider shadow-glow-sm">
                        {badge}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              <div className="text-center mb-4">
                <span className="text-3xl font-extrabold gradient-text">{priceStr}</span>
                <p className="text-[11px] text-slate-600 mt-1">USD &middot; Secure Stripe checkout</p>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handlePayment}
                disabled={loading}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold text-white transition-all",
                  loading
                    ? "bg-deep-200 text-slate-600 cursor-not-allowed"
                    : "btn-glow"
                )}
              >
                {loading ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Redirecting&hellip;</>
                ) : (
                  <><CreditCard className="h-4 w-4" /> Pay {priceStr} &amp; Download</>
                )}
              </motion.button>

              <div className="flex items-center justify-center gap-4 mt-3 text-[11px] text-slate-600">
                <span className="flex items-center gap-1"><Lock className="h-3 w-3" /> Secure</span>
                <span className="flex items-center gap-1"><CreditCard className="h-3 w-3" /> Stripe</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
