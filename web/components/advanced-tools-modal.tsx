"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, Eraser, Wand2, ZoomIn, ZoomOut, RotateCcw, Check, Loader2,
  Undo2, Redo2, Maximize2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_HISTORY = 30;

export type ToolMode = "magnify" | "erase" | "fill";

interface Props {
  open: boolean;
  srcUrl: string;
  bgColor: [number, number, number];
  mode: ToolMode;
  onApply: (newDataUrl: string) => void;
  onClose: () => void;
}

const MODE_COPY: Record<ToolMode, { title: string; help: string }> = {
  magnify: { title: "Magnify", help: "Click to zoom in \u00b7 Alt+click to zoom out \u00b7 Scroll to zoom \u00b7 Space+drag to pan" },
  erase: { title: "Erase", help: "Paint to erase with background color \u00b7 [ / ] resize brush \u00b7 Space+drag to pan \u00b7 Ctrl+Z undo" },
  fill: { title: "Content-aware Fill", help: "Paint over marks, then click Fill \u00b7 [ / ] resize brush \u00b7 Space+drag to pan \u00b7 Ctrl+Z undo" },
};

export default function AdvancedToolsModal({ open, srcUrl, bgColor, mode, onApply, onClose }: Props) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const workingRef = useRef<HTMLCanvasElement>(null);
  const maskRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [brush, setBrush] = useState(30);
  const [hasMask, setHasMask] = useState(false);
  const [filling, setFilling] = useState(false);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const [vpSize, setVpSize] = useState({ w: 0, h: 0 });
  const [spaceHeld, setSpaceHeld] = useState(false);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
  const [historyLen, setHistoryLen] = useState(0);
  const [historyIdx, setHistoryIdx] = useState(-1);

  const effectiveTool: "pan" | "paint" = spaceHeld || mode === "magnify" ? "pan" : "paint";

  const historyRef = useRef<ImageData[]>([]);
  const historyIdxRef = useRef(-1);

  const pushHistory = useCallback(() => {
    const working = workingRef.current;
    if (!working) return;
    const ctx = working.getContext("2d");
    if (!ctx) return;
    const snap = ctx.getImageData(0, 0, working.width, working.height);
    historyRef.current = historyRef.current.slice(0, historyIdxRef.current + 1);
    historyRef.current.push(snap);
    if (historyRef.current.length > MAX_HISTORY) historyRef.current.shift();
    historyIdxRef.current = historyRef.current.length - 1;
    setHistoryLen(historyRef.current.length);
    setHistoryIdx(historyIdxRef.current);
  }, []);

  const restoreFromHistory = useCallback((idx: number) => {
    const working = workingRef.current;
    if (!working) return;
    const ctx = working.getContext("2d");
    const snap = historyRef.current[idx];
    if (!ctx || !snap) return;
    ctx.putImageData(snap, 0, 0);
  }, []);

  const undo = useCallback(() => {
    if (historyIdxRef.current <= 0) return;
    historyIdxRef.current -= 1;
    restoreFromHistory(historyIdxRef.current);
    setHistoryIdx(historyIdxRef.current);
  }, [restoreFromHistory]);

  const redo = useCallback(() => {
    if (historyIdxRef.current >= historyRef.current.length - 1) return;
    historyIdxRef.current += 1;
    restoreFromHistory(historyIdxRef.current);
    setHistoryIdx(historyIdxRef.current);
  }, [restoreFromHistory]);

  useEffect(() => {
    if (!open) return;
    const vp = viewportRef.current;
    if (!vp) return;
    const measure = () => { const r = vp.getBoundingClientRect(); setVpSize({ w: r.width, h: r.height }); };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(vp);
    return () => ro.disconnect();
  }, [open]);

  const loadedImgRef = useRef<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!open) return;
    const img = new Image();
    if (!srcUrl.startsWith("data:")) img.crossOrigin = "anonymous";
    img.onload = () => {
      loadedImgRef.current = img;
      setImgSize({ w: img.naturalWidth, h: img.naturalHeight });
      setHasMask(false);
      setZoom(1);
      setPan({ x: 0, y: 0 });
      historyRef.current = [];
      historyIdxRef.current = -1;
      setHistoryLen(0);
      setHistoryIdx(-1);
    };
    img.src = srcUrl;
  }, [open, srcUrl]);

  useEffect(() => {
    const img = loadedImgRef.current;
    if (!img || imgSize.w === 0) return;
    for (const ref of [workingRef, maskRef, overlayRef]) {
      const c = ref.current;
      if (!c) return;
      c.width = imgSize.w;
      c.height = imgSize.h;
    }
    const wctx = workingRef.current?.getContext("2d");
    wctx?.drawImage(img, 0, 0);
    maskRef.current?.getContext("2d")?.clearRect(0, 0, imgSize.w, imgSize.h);
    overlayRef.current?.getContext("2d")?.clearRect(0, 0, imgSize.w, imgSize.h);
    pushHistory();
  }, [imgSize, pushHistory]);

  useEffect(() => {
    if (!open) return;
    const isEditable = (el: EventTarget | null) => {
      if (!el || !(el instanceof HTMLElement)) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || el.isContentEditable;
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (isEditable(e.target)) return;
      if (e.code === "Space") { e.preventDefault(); setSpaceHeld(true); return; }
      if ((e.ctrlKey || e.metaKey) && e.code === "KeyZ") { e.preventDefault(); if (e.shiftKey) redo(); else undo(); return; }
      if ((e.ctrlKey || e.metaKey) && e.code === "KeyY") { e.preventDefault(); redo(); return; }
      if (e.key === "[") { e.preventDefault(); setBrush((b) => Math.max(4, b - 4)); }
      else if (e.key === "]") { e.preventDefault(); setBrush((b) => Math.min(200, b + 4)); }
      else if (e.key === "Escape") onClose();
    };
    const onKeyUp = (e: KeyboardEvent) => { if (e.code === "Space") setSpaceHeld(false); };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => { window.removeEventListener("keydown", onKeyDown); window.removeEventListener("keyup", onKeyUp); };
  }, [open, undo, redo, onClose]);

  const baseScale = vpSize.w > 0 && imgSize.w > 0 ? Math.min(vpSize.w / imgSize.w, vpSize.h / imgSize.h) : 1;
  const drawnW = imgSize.w * baseScale * zoom;
  const drawnH = imgSize.h * baseScale * zoom;
  const imgLeft = vpSize.w / 2 + pan.x - drawnW / 2;
  const imgTop = vpSize.h / 2 + pan.y - drawnH / 2;

  const viewportToImage = useCallback(
    (clientX: number, clientY: number) => {
      const vp = viewportRef.current;
      if (!vp || imgSize.w === 0 || vpSize.w === 0) return null;
      const rect = vp.getBoundingClientRect();
      const imgX = ((clientX - rect.left - imgLeft) / drawnW) * imgSize.w;
      const imgY = ((clientY - rect.top - imgTop) / drawnH) * imgSize.h;
      return { x: imgX, y: imgY };
    },
    [imgSize, vpSize, imgLeft, imgTop, drawnW, drawnH],
  );

  const strokeBetween = useCallback(
    (from: { x: number; y: number }, to: { x: number; y: number }) => {
      const mctx = maskRef.current?.getContext("2d");
      const octx = overlayRef.current?.getContext("2d");
      if (!mctx || !octx) return;
      const draw = (ctx: CanvasRenderingContext2D, style: string) => {
        ctx.strokeStyle = style; ctx.fillStyle = style;
        ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.lineWidth = brush;
        ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke();
        ctx.beginPath(); ctx.arc(to.x, to.y, brush / 2, 0, Math.PI * 2); ctx.fill();
      };
      draw(mctx, "rgba(255,255,255,1)");
      if (mode === "erase") {
        const wctx = workingRef.current?.getContext("2d");
        if (wctx) { const [R, G, B] = bgColor; draw(wctx, `rgb(${R},${G},${B})`); }
      } else {
        draw(octx, "rgba(0,212,255,0.45)");
      }
      setHasMask(true);
    },
    [brush, mode, bgColor],
  );

  const paintingRef = useRef(false);
  const lastPtRef = useRef<{ x: number; y: number } | null>(null);
  const panDragRef = useRef<{ startX: number; startY: number; basePan: { x: number; y: number }; moved: boolean } | null>(null);

  const onPointerDown = (e: React.PointerEvent) => {
    (e.target as Element).setPointerCapture(e.pointerId);
    if (effectiveTool === "pan") { panDragRef.current = { startX: e.clientX, startY: e.clientY, basePan: pan, moved: false }; return; }
    const pt = viewportToImage(e.clientX, e.clientY);
    if (!pt) return;
    paintingRef.current = true;
    lastPtRef.current = pt;
    strokeBetween(pt, pt);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    setCursorPos({ x: e.clientX, y: e.clientY });
    if (panDragRef.current) {
      const drag = panDragRef.current;
      const dx = e.clientX - drag.startX;
      const dy = e.clientY - drag.startY;
      if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
      setPan({ x: drag.basePan.x + dx, y: drag.basePan.y + dy });
      return;
    }
    if (!paintingRef.current) return;
    const pt = viewportToImage(e.clientX, e.clientY);
    if (!pt || !lastPtRef.current) return;
    strokeBetween(lastPtRef.current, pt);
    lastPtRef.current = pt;
  };

  const onPointerUp = (e: React.PointerEvent) => {
    if (panDragRef.current) {
      const drag = panDragRef.current;
      panDragRef.current = null;
      if (mode === "magnify" && !drag.moved && !spaceHeld) {
        const pt = viewportToImage(e.clientX, e.clientY);
        if (pt && pt.x >= 0 && pt.y >= 0 && pt.x <= imgSize.w && pt.y <= imgSize.h) {
          const newZoom = e.altKey ? Math.max(1, zoom - 0.75) : zoom < 1.5 ? 2.5 : Math.min(8, zoom + 0.75);
          const newDrawnW = imgSize.w * baseScale * newZoom;
          const newDrawnH = imgSize.h * baseScale * newZoom;
          setZoom(newZoom);
          setPan({ x: (pt.x / imgSize.w - 0.5) * -newDrawnW, y: (pt.y / imgSize.h - 0.5) * -newDrawnH });
        }
      }
    }
    if (paintingRef.current) { paintingRef.current = false; lastPtRef.current = null; pushHistory(); }
  };

  const onWheel = (e: React.WheelEvent) => {
    if (!vpSize.w || !imgSize.w) return;
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    const newZoom = Math.max(1, Math.min(8, zoom * zoomFactor));
    if (newZoom === zoom) return;
    const rect = viewportRef.current!.getBoundingClientRect();
    const vx = e.clientX - rect.left;
    const vy = e.clientY - rect.top;
    const imgX = ((vx - imgLeft) / drawnW) * imgSize.w;
    const imgY = ((vy - imgTop) / drawnH) * imgSize.h;
    const newDrawnW = imgSize.w * baseScale * newZoom;
    const newDrawnH = imgSize.h * baseScale * newZoom;
    setZoom(newZoom);
    setPan({ x: vx - (imgX / imgSize.w) * newDrawnW + newDrawnW / 2 - vpSize.w / 2, y: vy - (imgY / imgSize.h) * newDrawnH + newDrawnH / 2 - vpSize.h / 2 });
  };

  const zoomBy = (factor: number) => setZoom((z) => Math.max(1, Math.min(8, z * factor)));
  const resetView = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  const clearMask = () => {
    maskRef.current?.getContext("2d")?.clearRect(0, 0, imgSize.w, imgSize.h);
    overlayRef.current?.getContext("2d")?.clearRect(0, 0, imgSize.w, imgSize.h);
    setHasMask(false);
  };

  const applyContentAwareFill = async () => {
    const working = workingRef.current;
    const mask = maskRef.current;
    if (!working || !mask) return;
    setFilling(true);
    try {
      const image_b64 = working.toDataURL("image/jpeg", 0.95);
      const mask_b64 = mask.toDataURL("image/png");
      const res = await fetch(`${API_URL}/api/inpaint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64, mask_b64, radius: 5 }),
      });
      if (!res.ok) throw new Error(`Server ${res.status}`);
      const data = await res.json();
      const img = new Image();
      img.onload = () => {
        const wctx = working.getContext("2d");
        if (wctx) wctx.drawImage(img, 0, 0, working.width, working.height);
        clearMask();
        pushHistory();
        setFilling(false);
      };
      img.onerror = () => { setFilling(false); alert("Failed to load inpainted image"); };
      img.src = data.image_b64;
    } catch (err) { setFilling(false); alert(`Fill failed: ${err instanceof Error ? err.message : "unknown"}`); }
  };

  const commit = () => {
    const working = workingRef.current;
    if (!working) return;
    onApply(working.toDataURL("image/jpeg", 0.95));
    onClose();
  };

  const canUndo = historyIdx > 0;
  const canRedo = historyIdx >= 0 && historyIdx < historyLen - 1;
  const brushScreenPx = brush * baseScale * zoom;
  const viewportCursor = effectiveTool === "pan"
    ? (spaceHeld ? "cursor-grab" : mode === "magnify" ? "cursor-zoom-in" : "cursor-grab")
    : "cursor-none";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-deep-100 rounded-2xl shadow-2xl border border-[rgba(0,212,255,0.1)] w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-[rgba(0,212,255,0.08)]">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                {mode === "magnify" && <ZoomIn className="h-4 w-4 text-accent-300" />}
                {mode === "erase" && <Eraser className="h-4 w-4 text-accent-300" />}
                {mode === "fill" && <Wand2 className="h-4 w-4 text-accent-300" />}
                {MODE_COPY[mode].title}
              </h2>
              <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:text-white hover:bg-deep-200">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-2 px-5 py-2.5 bg-deep-50 border-b border-[rgba(0,212,255,0.06)] text-sm">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold text-slate-500">Zoom</span>
                <button onClick={() => zoomBy(1 / 1.25)} className="flex h-7 w-7 items-center justify-center rounded bg-deep-100 border border-[rgba(0,212,255,0.08)] hover:bg-deep-200 text-slate-400" title="Zoom out">
                  <ZoomOut className="h-3.5 w-3.5" />
                </button>
                <span className="text-[11px] font-semibold text-slate-400 tabular-nums w-10 text-center">{Math.round(zoom * 100)}%</span>
                <button onClick={() => zoomBy(1.25)} className="flex h-7 w-7 items-center justify-center rounded bg-deep-100 border border-[rgba(0,212,255,0.08)] hover:bg-deep-200 text-slate-400" title="Zoom in">
                  <ZoomIn className="h-3.5 w-3.5" />
                </button>
                <button onClick={resetView} className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-deep-200" title="Fit">
                  <Maximize2 className="h-3 w-3" /> Fit
                </button>
              </div>

              {mode !== "magnify" && (
                <>
                  <div className="h-5 w-px bg-[rgba(0,212,255,0.08)] mx-1" />
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-slate-500">Brush</span>
                    <input type="range" min={4} max={200} step={1} value={brush} onChange={(e) => setBrush(parseInt(e.target.value))} className="w-24" />
                    <span className="text-[11px] text-slate-500 tabular-nums w-8">{brush}px</span>
                  </div>
                </>
              )}

              <div className="h-5 w-px bg-[rgba(0,212,255,0.08)] mx-1" />
              <div className="flex items-center gap-1">
                <button onClick={undo} disabled={!canUndo} className={cn("flex h-7 w-7 items-center justify-center rounded border", canUndo ? "bg-deep-100 border-[rgba(0,212,255,0.08)] text-slate-400 hover:bg-deep-200" : "bg-deep-50 border-transparent text-slate-700 cursor-not-allowed")} title="Undo">
                  <Undo2 className="h-3.5 w-3.5" />
                </button>
                <button onClick={redo} disabled={!canRedo} className={cn("flex h-7 w-7 items-center justify-center rounded border", canRedo ? "bg-deep-100 border-[rgba(0,212,255,0.08)] text-slate-400 hover:bg-deep-200" : "bg-deep-50 border-transparent text-slate-700 cursor-not-allowed")} title="Redo">
                  <Redo2 className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="flex-1" />

              {mode === "fill" && (
                <>
                  <button onClick={clearMask} disabled={!hasMask} className={cn("rounded px-3 py-1.5 text-[11px] font-semibold border", hasMask ? "bg-deep-100 border-[rgba(0,212,255,0.08)] text-slate-400 hover:bg-deep-200" : "bg-deep-50 border-transparent text-slate-700 cursor-not-allowed")}>
                    Clear mask
                  </button>
                  <button onClick={applyContentAwareFill} disabled={!hasMask || filling} className={cn("flex items-center gap-1.5 rounded px-3 py-1.5 text-[11px] font-semibold", hasMask && !filling ? "btn-glow text-white" : "bg-deep-200 text-slate-600 cursor-not-allowed")} title="Reconstruct painted area">
                    {filling ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wand2 className="h-3.5 w-3.5" />} Fill
                  </button>
                </>
              )}
            </div>

            {/* Canvas viewport */}
            <div
              ref={viewportRef}
              className={cn(
                "relative flex-1 overflow-hidden select-none",
                "bg-[linear-gradient(45deg,#0D1B2A_25%,transparent_25%),linear-gradient(-45deg,#0D1B2A_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#0D1B2A_75%),linear-gradient(-45deg,transparent_75%,#0D1B2A_75%)]",
                "bg-[length:20px_20px] bg-[position:0_0,0_10px,10px_-10px,-10px_0] bg-deep",
                viewportCursor,
              )}
              style={{ minHeight: "55vh", touchAction: "none" }}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
              onPointerLeave={() => setCursorPos(null)}
              onWheel={onWheel}
            >
              <div className="absolute pointer-events-none" style={{ left: imgLeft, top: imgTop, width: drawnW, height: drawnH }}>
                <canvas ref={workingRef} className="absolute inset-0 w-full h-full" style={{ imageRendering: zoom >= 2 ? "pixelated" : "auto" }} />
                <canvas ref={overlayRef} className="absolute inset-0 w-full h-full" />
              </div>
              <canvas ref={maskRef} className="hidden" />

              {effectiveTool === "paint" && cursorPos && (() => {
                const rect = viewportRef.current?.getBoundingClientRect();
                if (!rect) return null;
                return (
                  <div
                    className="absolute pointer-events-none rounded-full border-2 border-accent-300/60"
                    style={{
                      left: cursorPos.x - rect.left - brushScreenPx / 2,
                      top: cursorPos.y - rect.top - brushScreenPx / 2,
                      width: brushScreenPx,
                      height: brushScreenPx,
                      boxShadow: "0 0 6px rgba(0,212,255,0.3)",
                    }}
                  />
                );
              })()}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-[rgba(0,212,255,0.06)] bg-deep-50">
              <p className="text-[11px] text-slate-500 max-w-2xl">{MODE_COPY[mode].help}</p>
              <div className="flex items-center gap-2">
                <button onClick={onClose} className="btn-ghost rounded-lg px-4 py-2 text-xs font-medium text-slate-300">Cancel</button>
                <button onClick={commit} className="flex items-center gap-1.5 btn-glow rounded-lg px-4 py-2 text-xs font-bold text-white">
                  <Check className="h-4 w-4" /> Apply
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
