"use client";

import { useMemo, useState } from "react";
import { Sparkles, Camera, RotateCcw, Wand2, ZoomIn, Eraser } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import AdvancedToolsModal, { type ToolMode } from "@/components/advanced-tools-modal";

export type Variant = "enhanced" | "original";

export interface Edits {
  brightness: number;
  contrast: number;
  saturation: number;
  warmth: number;
}

export const DEFAULT_EDITS: Edits = {
  brightness: 1,
  contrast: 1,
  saturation: 1,
  warmth: 0,
};

export interface CropAdjust {
  x: number;
  y: number;
  zoom: number;
}

export const DEFAULT_CROP: CropAdjust = { x: 0, y: 0, zoom: 1 };

export function cropToCssTransform(c: CropAdjust): string {
  if (c.x === 0 && c.y === 0 && c.zoom === 1) return "none";
  return `scale(${c.zoom}) translate(${c.x}%, ${c.y}%)`;
}

export async function bakeCropToDataUrl(
  srcDataUrl: string,
  crop: CropAdjust,
  bgColor: [number, number, number] = [255, 255, 255],
  format: "jpeg" | "png" = "jpeg",
): Promise<string> {
  if (crop.x === 0 && crop.y === 0 && crop.zoom === 1) return srcDataUrl;
  return new Promise((resolve, reject) => {
    const img = new Image();
    if (!srcDataUrl.startsWith("data:")) img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return reject(new Error("canvas unsupported"));
      ctx.fillStyle = `rgb(${bgColor[0]},${bgColor[1]},${bgColor[2]})`;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      ctx.translate(cx, cy);
      ctx.scale(crop.zoom, crop.zoom);
      ctx.translate(-cx + (crop.x / 100) * canvas.width, -cy + (crop.y / 100) * canvas.height);
      ctx.drawImage(img, 0, 0);
      resolve(canvas.toDataURL(format === "png" ? "image/png" : "image/jpeg", 0.95));
    };
    img.onerror = () => reject(new Error("image load failed"));
    img.src = srcDataUrl;
  });
}

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

function dataUrlBytes(dataUrl: string): number {
  const comma = dataUrl.indexOf(",");
  const b64 = comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
  const pad = b64.endsWith("==") ? 2 : b64.endsWith("=") ? 1 : 0;
  return Math.floor((b64.length * 3) / 4) - pad;
}

export async function fitJpegUnderKB(dataUrl: string, maxKB: number): Promise<string> {
  const target = maxKB * 1024;
  if (dataUrlBytes(dataUrl) <= target) return dataUrl;
  return new Promise((resolve, reject) => {
    const img = new Image();
    if (!dataUrl.startsWith("data:")) img.crossOrigin = "anonymous";
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      const ctx = c.getContext("2d");
      if (!ctx) return reject(new Error("canvas unsupported"));
      ctx.drawImage(img, 0, 0);
      let lo = 0.3, hi = 0.95;
      let best = c.toDataURL("image/jpeg", hi);
      if (dataUrlBytes(best) <= target) return resolve(best);
      for (let i = 0; i < 8; i++) {
        const q = (lo + hi) / 2;
        const candidate = c.toDataURL("image/jpeg", q);
        if (dataUrlBytes(candidate) <= target) { best = candidate; lo = q; } else { hi = q; }
      }
      resolve(best);
    };
    img.onerror = () => reject(new Error("image load failed"));
    img.src = dataUrl;
  });
}

export async function bakeEditsToDataUrl(
  srcDataUrl: string, edits: Edits, format: "jpeg" | "png" = "jpeg",
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

export interface PrintSheetOptions {
  orientation?: "landscape" | "portrait";
  cols?: number;
  rows?: number;
  separator_mm?: number;
  y_offset_mm?: number;
}

export async function buildPrintSheet(
  photoDataUrl: string, widthMm: number, heightMm: number,
  dpi: number, format: "jpeg" | "png" = "jpeg", options: PrintSheetOptions = {},
): Promise<string> {
  const mmToPx = (mm: number) => Math.round((mm * dpi) / 25.4);
  const orientation = options.orientation ?? "landscape";
  const sheetW = (orientation === "portrait" ? 4 : 6) * dpi;
  const sheetH = (orientation === "portrait" ? 6 : 4) * dpi;
  const margin = mmToPx(2);
  const cols = options.cols ?? 3;
  const rows = options.rows ?? 2;
  let photoW = mmToPx(widthMm);
  let photoH = mmToPx(heightMm);
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
      c.width = sheetW; c.height = sheetH;
      const ctx = c.getContext("2d");
      if (!ctx) return reject(new Error("canvas unsupported"));
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, sheetW, sheetH);
      ctx.imageSmoothingQuality = "high";
      const totalW = cols * photoW + (cols - 1) * margin;
      const totalH = rows * photoH + (rows - 1) * margin;
      const startX = Math.max(margin, Math.floor((sheetW - totalW) / 2));
      const yOffsetPx = options.y_offset_mm ? mmToPx(options.y_offset_mm) : 0;
      const maxStartY = sheetH - totalH - margin;
      const startY = Math.max(margin, Math.min(Math.floor((sheetH - totalH) / 2) + yOffsetPx, maxStartY));
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = startX + col * (photoW + margin);
          const y = startY + row * (photoH + margin);
          if (x + photoW <= sheetW && y + photoH <= sheetH) ctx.drawImage(img, x, y, photoW, photoH);
        }
      }
      ctx.strokeStyle = "rgb(180,180,180)";
      ctx.lineWidth = options.separator_mm ? Math.max(1, Math.round(mmToPx(options.separator_mm))) : Math.max(1, Math.floor(dpi / 175));
      const gridW = cols * photoW + (cols - 1) * margin;
      const gridH = rows * photoH + (rows - 1) * margin;
      for (let col = 1; col < cols; col++) {
        const x = startX + col * photoW + (col - 1) * margin + Math.floor(margin / 2);
        ctx.beginPath(); ctx.moveTo(x, startY); ctx.lineTo(x, startY + gridH); ctx.stroke();
      }
      for (let row = 1; row < rows; row++) {
        const y = startY + row * photoH + (row - 1) * margin + Math.floor(margin / 2);
        ctx.beginPath(); ctx.moveTo(startX, y); ctx.lineTo(startX + gridW, y); ctx.stroke();
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
  previewUrl: string;
  advancedSrcUrl?: string;
  compact?: boolean;
  bgColor?: [number, number, number];
  onAdvancedApply?: (newDataUrl: string) => void;
}

export default function PhotoEditor({
  variant, onVariantChange, edits, onEditsChange,
  previewUrl, advancedSrcUrl, compact = false, bgColor, onAdvancedApply,
}: Props) {
  const { t } = useTranslation();
  const filter = useMemo(() => editsToCssFilter(edits), [edits]);
  const [activeMode, setActiveMode] = useState<ToolMode | null>(null);
  const update = (patch: Partial<Edits>) => onEditsChange({ ...edits, ...patch });
  const reset = () => onEditsChange(DEFAULT_EDITS);

  return (
    <div className="space-y-3">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{t("editor.version")}</label>
          <button
            onClick={reset}
            className="flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-accent-300 transition-colors"
            type="button"
          >
            <RotateCcw className="h-3 w-3" /> {t("editor.reset")}
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onVariantChange("enhanced")}
            className={cn(
              "flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all",
              variant === "enhanced"
                ? "border-accent-300/30 bg-accent-50 text-accent-300"
                : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]",
            )}
          >
            <Sparkles className="h-3 w-3" /> {t("editor.aiEnhanced")}
          </button>
          <button
            type="button"
            onClick={() => onVariantChange("original")}
            className={cn(
              "flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all",
              variant === "original"
                ? "border-accent-300/30 bg-accent-50 text-accent-300"
                : "border-[rgba(0,212,255,0.08)] bg-deep-100 text-slate-400 hover:border-[rgba(0,212,255,0.15)]",
            )}
          >
            <Camera className="h-3 w-3" /> {t("editor.croppedOnly")}
          </button>
        </div>
      </div>

      {!compact && (
        <div className="rounded-lg overflow-hidden bg-deep-200 border border-[rgba(0,212,255,0.06)] shadow-sm flex items-center justify-center">
          <img src={previewUrl} alt="Edit preview" className="max-h-72 object-contain" style={{ filter }} />
        </div>
      )}

      <div className="space-y-2.5">
        <Slider label={t("editor.brightness")} value={edits.brightness} min={0.6} max={1.4} step={0.01} formatValue={(v) => `${Math.round((v - 1) * 100)}`} onChange={(v) => update({ brightness: v })} />
        <Slider label={t("editor.contrast")} value={edits.contrast} min={0.6} max={1.4} step={0.01} formatValue={(v) => `${Math.round((v - 1) * 100)}`} onChange={(v) => update({ contrast: v })} />
        <Slider label={t("editor.saturation")} value={edits.saturation} min={0.5} max={1.5} step={0.01} formatValue={(v) => `${Math.round((v - 1) * 100)}`} onChange={(v) => update({ saturation: v })} />
        <Slider label={t("editor.warmth")} value={edits.warmth} min={-30} max={30} step={1} formatValue={(v) => `${v > 0 ? "+" : ""}${Math.round(v)}`} onChange={(v) => update({ warmth: v })} />
      </div>

      {onAdvancedApply && (
        <div>
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">{t("editor.advancedTools")}</label>
          <div className="grid grid-cols-3 gap-2">
            <ToolLauncher icon={ZoomIn} label={t("editor.magnify")} onClick={() => setActiveMode("magnify")} />
            <ToolLauncher icon={Eraser} label={t("editor.erase")} onClick={() => setActiveMode("erase")} />
            <ToolLauncher icon={Wand2} label={t("editor.fill")} onClick={() => setActiveMode("fill")} />
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

function ToolLauncher({ icon: Icon, label, onClick }: { icon: React.ComponentType<{ className?: string }>; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-accent-300/20 bg-accent-50/50 py-2 text-[11px] font-semibold text-accent-300 hover:bg-accent-50 hover:border-accent-300/30 transition-all"
    >
      <Icon className="h-3.5 w-3.5" /> {label}
    </button>
  );
}

interface SliderProps {
  label: string; value: number; min: number; max: number; step: number;
  onChange: (v: number) => void; formatValue: (v: number) => string;
}

function Slider({ label, value, min, max, step, onChange, formatValue }: SliderProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-semibold text-slate-400">{label}</span>
        <span className="text-[11px] text-slate-500 tabular-nums">{formatValue(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full"
      />
    </div>
  );
}
