"use client";

/**
 * PhotoEditor — lets the user pick between the AI-Enhanced and the
 * Original (no-AI) variant of the processed photo, and fine-tune
 * brightness / contrast / warmth / saturation with live sliders.
 *
 * The preview is a plain <img> with a CSS filter for zero-latency
 * feedback. On download, bakeEditsToDataUrl() re-applies the same
 * filter via a <canvas> so the downloaded file matches what the user
 * sees on screen.
 */

import { useMemo, useState } from "react";
import { Sparkles, Camera, RotateCcw, Wand2, ZoomIn, Eraser } from "lucide-react";
import { cn } from "@/lib/utils";
import AdvancedToolsModal, { type ToolMode } from "@/components/advanced-tools-modal";

export type Variant = "enhanced" | "original";

export interface Edits {
  brightness: number; // 0.5 .. 1.5 (1 = untouched)
  contrast: number;   // 0.5 .. 1.5
  saturation: number; // 0.5 .. 1.5
  warmth: number;     // -30 .. 30 (hue rotate degrees; - cools, + warms)
}

export const DEFAULT_EDITS: Edits = {
  brightness: 1,
  contrast: 1,
  saturation: 1,
  warmth: 0,
};

export function editsToCssFilter(e: Edits): string {
  return [
    `brightness(${e.brightness})`,
    `contrast(${e.contrast})`,
    `saturate(${e.saturation})`,
    e.warmth !== 0 ? `hue-rotate(${-e.warmth / 6}deg) sepia(${Math.abs(e.warmth) / 100})` : "",
  ]
    .filter(Boolean)
    .join(" ");
}

/** Bake the CSS filter into a new data URL by drawing to canvas. */
export async function bakeEditsToDataUrl(
  srcDataUrl: string,
  edits: Edits,
  format: "jpeg" | "png" = "jpeg",
): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    if (!srcDataUrl.startsWith("data:")) img.crossOrigin = "anonymous";
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      const ctx = c.getContext("2d");
      if (!ctx) return reject(new Error("canvas unsupported"));
      ctx.filter = editsToCssFilter(edits);
      ctx.drawImage(img, 0, 0);
      resolve(c.toDataURL(format === "png" ? "image/png" : "image/jpeg", 0.95));
    };
    img.onerror = () => reject(new Error("image load failed"));
    img.src = srcDataUrl;
  });
}

/**
 * Build a 4×6" print sheet (3×2 tiled = 6 photos) from a single photo
 * data URL, with thin grey separator lines between cells. Mirrors the
 * server's processing/print_sheet.py so edited photos can be re-tiled
 * on the client without a round-trip.
 */
export async function buildPrintSheet(
  photoDataUrl: string,
  widthMm: number,
  heightMm: number,
  dpi: number,
  format: "jpeg" | "png" = "jpeg",
): Promise<string> {
  const mmToPx = (mm: number) => Math.round((mm * dpi) / 25.4);
  const sheetW = 6 * dpi;
  const sheetH = 4 * dpi;
  const margin = mmToPx(2);
  const cols = 3, rows = 2;

  let photoW = mmToPx(widthMm);
  let photoH = mmToPx(heightMm);
  // Auto-scale if the requested size doesn't fit 6-up on a 6×4" sheet.
  const availW = sheetW - 2 * margin - (cols - 1) * margin;
  const availH = sheetH - 2 * margin - (rows - 1) * margin;
  const maxW = Math.floor(availW / cols);
  const maxH = Math.floor(availH / rows);
  if (photoW > maxW || photoH > maxH) {
    const scale = Math.min(maxW / photoW, maxH / photoH);
    photoW = Math.floor(photoW * scale);
    photoH = Math.floor(photoH * scale);
  }

  return new Promise((resolve, reject) => {
    const img = new Image();
    if (!photoDataUrl.startsWith("data:")) img.crossOrigin = "anonymous";
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = sheetW;
      c.height = sheetH;
      const ctx = c.getContext("2d");
      if (!ctx) return reject(new Error("canvas unsupported"));
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, sheetW, sheetH);
      ctx.imageSmoothingQuality = "high";

      const totalW = cols * photoW + (cols - 1) * margin;
      const totalH = rows * photoH + (rows - 1) * margin;
      const startX = Math.max(margin, Math.floor((sheetW - totalW) / 2));
      const startY = Math.max(margin, Math.floor((sheetH - totalH) / 2));

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = startX + col * (photoW + margin);
          const y = startY + row * (photoH + margin);
          if (x + photoW <= sheetW && y + photoH <= sheetH) {
            ctx.drawImage(img, x, y, photoW, photoH);
          }
        }
      }

      // Thin grey separator lines between rows / columns.
      ctx.strokeStyle = "rgb(180,180,180)";
      ctx.lineWidth = Math.max(1, Math.floor(dpi / 175));
      const gridW = cols * photoW + (cols - 1) * margin;
      const gridH = rows * photoH + (rows - 1) * margin;
      for (let col = 1; col < cols; col++) {
        const x = startX + col * photoW + (col - 1) * margin + Math.floor(margin / 2);
        ctx.beginPath();
        ctx.moveTo(x, startY); ctx.lineTo(x, startY + gridH);
        ctx.stroke();
      }
      for (let row = 1; row < rows; row++) {
        const y = startY + row * photoH + (row - 1) * margin + Math.floor(margin / 2);
        ctx.beginPath();
        ctx.moveTo(startX, y); ctx.lineTo(startX + gridW, y);
        ctx.stroke();
      }

      resolve(c.toDataURL(format === "png" ? "image/png" : "image/jpeg", 0.95));
    };
    img.onerror = () => reject(new Error("image load failed"));
    img.src = photoDataUrl;
  });
}

interface Props {
  variant: Variant;
  onVariantChange: (v: Variant) => void;
  edits: Edits;
  onEditsChange: (e: Edits) => void;
  /** Crisp 600-DPI preview URL of the currently chosen variant */
  previewUrl: string;
  /** URL to edit with magnify/erase/fill. Typically the AI-enhanced
   *  variant so the tools always act on the highest-quality image,
   *  regardless of which variant is currently being viewed. */
  advancedSrcUrl?: string;
  compact?: boolean;
  /** Background color for local erase (must match the spec). */
  bgColor?: [number, number, number];
  /** Fired when the user applies magnify/erase/fill edits. */
  onAdvancedApply?: (newDataUrl: string) => void;
}

export default function PhotoEditor({
  variant,
  onVariantChange,
  edits,
  onEditsChange,
  previewUrl,
  advancedSrcUrl,
  compact = false,
  bgColor,
  onAdvancedApply,
}: Props) {
  const filter = useMemo(() => editsToCssFilter(edits), [edits]);
  const [activeMode, setActiveMode] = useState<ToolMode | null>(null);

  const update = (patch: Partial<Edits>) => onEditsChange({ ...edits, ...patch });
  const reset = () => onEditsChange(DEFAULT_EDITS);

  return (
    <div className="space-y-4">
      {/* Variant toggle */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Version
          </label>
          <button
            onClick={reset}
            className="flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-navy-600 transition-colors"
            type="button"
          >
            <RotateCcw className="h-3 w-3" />
            Reset edits
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onVariantChange("enhanced")}
            className={cn(
              "flex items-center justify-center gap-1.5 rounded-lg border py-2.5 text-sm font-semibold transition-all",
              variant === "enhanced"
                ? "border-teal-400 bg-teal-50 text-teal-700 ring-2 ring-teal-400/20"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
            )}
          >
            <Sparkles className="h-3.5 w-3.5" />
            AI Enhanced
          </button>
          <button
            type="button"
            onClick={() => onVariantChange("original")}
            className={cn(
              "flex items-center justify-center gap-1.5 rounded-lg border py-2.5 text-sm font-semibold transition-all",
              variant === "original"
                ? "border-teal-400 bg-teal-50 text-teal-700 ring-2 ring-teal-400/20"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
            )}
          >
            <Camera className="h-3.5 w-3.5" />
            Original
          </button>
        </div>
      </div>

      {/* Live preview */}
      {!compact && (
        <div className="rounded-lg overflow-hidden bg-white border border-slate-100 shadow-sm flex items-center justify-center">
          <img
            src={previewUrl}
            alt="Edit preview"
            className="max-h-72 object-contain"
            style={{ filter }}
          />
        </div>
      )}

      {/* Sliders */}
      <div className="space-y-3">
        <Slider
          label="Brightness"
          value={edits.brightness}
          min={0.6}
          max={1.4}
          step={0.01}
          formatValue={(v) => `${Math.round((v - 1) * 100)}`}
          onChange={(v) => update({ brightness: v })}
        />
        <Slider
          label="Contrast"
          value={edits.contrast}
          min={0.6}
          max={1.4}
          step={0.01}
          formatValue={(v) => `${Math.round((v - 1) * 100)}`}
          onChange={(v) => update({ contrast: v })}
        />
        <Slider
          label="Saturation"
          value={edits.saturation}
          min={0.5}
          max={1.5}
          step={0.01}
          formatValue={(v) => `${Math.round((v - 1) * 100)}`}
          onChange={(v) => update({ saturation: v })}
        />
        <Slider
          label="Warmth"
          value={edits.warmth}
          min={-30}
          max={30}
          step={1}
          formatValue={(v) => `${v > 0 ? "+" : ""}${Math.round(v)}`}
          onChange={(v) => update({ warmth: v })}
        />
      </div>

      {/* Three separate launchers — each opens the modal in its own mode */}
      {onAdvancedApply && (
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">
            Advanced tools
          </label>
          <div className="grid grid-cols-3 gap-2">
            <ToolLauncher
              icon={ZoomIn}
              label="Magnify"
              onClick={() => setActiveMode("magnify")}
            />
            <ToolLauncher
              icon={Eraser}
              label="Erase"
              onClick={() => setActiveMode("erase")}
            />
            <ToolLauncher
              icon={Wand2}
              label="Fill"
              onClick={() => setActiveMode("fill")}
            />
          </div>
        </div>
      )}

      {onAdvancedApply && activeMode && (
        <AdvancedToolsModal
          open={true}
          mode={activeMode}
          srcUrl={advancedSrcUrl ?? previewUrl}
          bgColor={bgColor ?? [255, 255, 255]}
          onApply={(url) => onAdvancedApply(url)}
          onClose={() => setActiveMode(null)}
        />
      )}
    </div>
  );
}

function ToolLauncher({
  icon: Icon,
  label,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-teal-300 bg-teal-50/50 py-2.5 text-xs font-semibold text-teal-700 hover:bg-teal-50 hover:border-teal-400 transition-all"
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  formatValue: (v: number) => string;
}

function Slider({ label, value, min, max, step, onChange, formatValue }: SliderProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-slate-600">{label}</span>
        <span className="text-xs text-slate-400 tabular-nums">{formatValue(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full bg-slate-200 accent-teal-500"
      />
    </div>
  );
}
