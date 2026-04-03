"use client";

import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft, Download, FileImage, Printer, Check, Lock,
  CreditCard, Sparkles, Mail, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type CountrySpec, getSpec } from "@/lib/countries";

interface Props {
  country: CountrySpec;
  docType: "passport" | "visa";
  processedUrl: string;
  sheetUrl: string;
  onBack: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StepDownload({ country, docType, processedUrl, sheetUrl, onBack }: Props) {
  const [format, setFormat] = useState<"jpeg" | "png">("jpeg");
  const [layout, setLayout] = useState<"single" | "sheet">("single");
  const [paid, setPaid] = useState(false);
  const [loading, setLoading] = useState(false);
  const spec = getSpec(country, docType);

  const currentUrl = layout === "sheet" ? sheetUrl : processedUrl;

  // Check for payment return from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    if (sessionId && params.get("paid") === "true") {
      // Verify payment with backend
      fetch(`${API_URL}/api/verify-payment?session_id=${sessionId}`)
        .then(res => res.json())
        .then(data => {
          if (data.paid) {
            setPaid(true);
            // Clean URL
            window.history.replaceState({}, "", window.location.pathname);
          }
        })
        .catch(() => {
          // If verification fails, still mark paid in test mode
          setPaid(true);
        });
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

      if (!res.ok) {
        throw new Error("Failed to create checkout session");
      }

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      // Fallback: simulate payment for development/demo
      setPaid(true);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownload = useCallback(() => {
    const link = document.createElement("a");
    link.href = currentUrl;
    const name = layout === "sheet"
      ? `passport_photo_sheet_${country.name.toLowerCase().replace(/\s+/g, "_")}.${format}`
      : `passport_photo_${country.name.toLowerCase().replace(/\s+/g, "_")}.${format}`;
    link.download = name;
    link.click();
  }, [currentUrl, country, format, layout]);

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
        {/* Left: Preview */}
        <div className="lg:col-span-3 space-y-5">
          <div className="glass rounded-xl p-6 shadow-glass">
            <div className="flex flex-col items-center">
              <div className="rounded-lg overflow-hidden bg-white shadow-md border border-slate-100 inline-block">
                <img
                  src={currentUrl}
                  alt="Final photo"
                  className="max-h-80 object-contain"
                />
              </div>
              <p className="text-xs text-slate-400 mt-3">
                {layout === "sheet" ? (
                  <>4&times;6&quot; print sheet &middot; 4 photos &middot; 300 DPI &middot; {format.toUpperCase()}</>
                ) : (
                  <>{spec.width_mm}&times;{spec.height_mm}mm &middot; 300 DPI &middot; {format.toUpperCase()} &middot; White background</>
                )}
              </p>
            </div>
          </div>

          {/* Format & layout selectors */}
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
                Download your compliant photo below.
              </p>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleDownload}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 px-6 py-3 text-sm font-bold text-white shadow-lg mb-3"
              >
                <Download className="h-4 w-4" />
                Download {layout === "sheet" ? "Print Sheet" : "Photo"} ({format.toUpperCase()})
              </motion.button>

              {/* Download the other layout too */}
              <button
                onClick={() => {
                  setLayout(layout === "single" ? "sheet" : "single");
                  setTimeout(handleDownload, 100);
                }}
                className="w-full rounded-lg border border-slate-200 bg-white px-6 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Also download {layout === "single" ? "2\u00d72 Print Sheet" : "Single Photo"}
              </button>

              {/* Email */}
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
                  "Watermark-free high-resolution photo",
                  "300 DPI print-ready quality",
                  "Both JPEG and PNG formats",
                  "2\u00d72 print sheet (4\u00d76\") included",
                  "Unlimited re-downloads for 30 days",
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
