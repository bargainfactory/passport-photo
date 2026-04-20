"use client";

import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload, Camera, Lightbulb, ArrowLeft, ArrowRight, X, RotateCcw, Square,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type CountrySpec, getSpec } from "@/lib/countries";
import FaceGuide from "@/components/face-guide";

interface Props {
  country: CountrySpec;
  docType: "passport" | "visa";
  onNext: (imageUrl: string) => void;
  onBack: () => void;
}

export default function StepUpload({ country, docType, onNext, onBack }: Props) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageSource, setImageSource] = useState<"file" | "webcam" | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showWebcam, setShowWebcam] = useState(false);
  const [webcamReady, setWebcamReady] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const spec = getSpec(country, docType);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      const img = new Image();
      img.onload = () => {
        setImageSource("file");
        const MAX_DIM = 2000;
        if (img.width <= MAX_DIM && img.height <= MAX_DIM) {
          setImageUrl(dataUrl);
          return;
        }
        const scale = MAX_DIM / Math.max(img.width, img.height);
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        canvas.getContext("2d")?.drawImage(img, 0, 0, canvas.width, canvas.height);
        setImageUrl(canvas.toDataURL("image/jpeg", 0.92));
      };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const startWebcam = async () => {
    setShowWebcam(true);
    setWebcamReady(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadeddata = () => setWebcamReady(true);
      }
    } catch {
      alert("Could not access webcam. Please allow camera access.");
      setShowWebcam(false);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const vw = videoRef.current.videoWidth;
    const vh = videoRef.current.videoHeight;
    if (!vw || !vh) return;
    const canvas = document.createElement("canvas");
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.translate(vw, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(videoRef.current, 0, 0);
    setImageUrl(canvas.toDataURL("image/jpeg", 0.95));
    setImageSource("webcam");
    stopWebcam();
  };

  const stopWebcam = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setShowWebcam(false);
    setWebcamReady(false);
  };

  const removeImage = () => { setImageUrl(null); setImageSource(null); };

  const retakeSelfie = () => {
    setImageUrl(null);
    setImageSource(null);
    startWebcam();
  };

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

      {/* Country badge */}
      <div className="inline-flex items-center gap-2 rounded-full bg-accent-50 border border-[rgba(0,212,255,0.1)] px-3 py-1 text-sm font-semibold text-accent-300 mb-4">
        <span className="text-base">{country.flag}</span>
        {country.name} &mdash; {docType.charAt(0).toUpperCase() + docType.slice(1)} &mdash;{" "}
        {spec.width_mm}&times;{spec.height_mm}mm
      </div>

      {/* Tips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
        <div className="glass rounded-xl p-3.5">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20 flex-shrink-0">
              <Lightbulb className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              <strong className="text-amber-300">Lighting:</strong> Face a window or soft lamp
              directly so light falls evenly. Avoid side lighting or flash.
            </div>
          </div>
        </div>
        <div className="glass rounded-xl p-3.5">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-300/10 border border-accent-300/20 flex-shrink-0">
              <Square className="h-4 w-4 text-accent-300" />
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              <strong className="text-accent-300">Background:</strong> Stand in front of a plain
              wall. Our AI will cleanly separate you from the scene.
            </div>
          </div>
        </div>
      </div>

      {imageUrl ? (
        <div className="glass rounded-xl p-5 text-center">
          <div className="relative inline-block">
            <img
              src={imageUrl}
              alt="Uploaded photo"
              className="rounded-lg max-h-72 mx-auto shadow-lg border border-[rgba(0,212,255,0.1)]"
            />
            <button
              onClick={removeImage}
              className="absolute -top-2 -right-2 flex h-7 w-7 items-center justify-center rounded-full bg-red-500 text-white shadow-md hover:bg-red-600 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="mt-4 rounded-lg bg-deep-200/50 border border-[rgba(0,212,255,0.06)] p-3 text-left max-w-sm mx-auto">
            <p className="text-xs font-semibold text-white/80 mb-1.5 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent-300" /> Pre-flight check
            </p>
            {[
              "Face clearly visible and front-facing",
              "Even lighting, no harsh shadows",
              "Neutral expression, eyes open",
              "Background (AI will replace it)",
            ].map((item) => (
              <div key={item} className="flex items-start gap-2 text-xs text-slate-400 py-0.5">
                <span className="text-accent-300 mt-0.5">&#10003;</span>
                {item}
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            {imageSource === "webcam" && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={retakeSelfie}
                className="btn-ghost inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-slate-300"
              >
                <RotateCcw className="h-4 w-4" /> Retake
              </motion.button>
            )}
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onNext(imageUrl)}
              className="btn-glow inline-flex items-center gap-2 rounded-xl px-8 py-3 text-sm font-bold text-white"
            >
              Process Photo <ArrowRight className="h-4 w-4" />
            </motion.button>
          </div>
        </div>
      ) : showWebcam ? (
        <div className="glass rounded-xl p-5 text-center">
          <div
            className="relative inline-block mx-auto rounded-lg overflow-hidden bg-black border border-[rgba(0,212,255,0.15)]"
            style={{ maxWidth: "480px", width: "100%" }}
          >
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full rounded-lg"
              style={{ transform: "scaleX(-1)" }}
            />
            {webcamReady && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="absolute inset-0"
              >
                <FaceGuide />
              </motion.div>
            )}
          </div>

          <div className="flex items-center justify-center gap-4 mt-4">
            <motion.button
              whileHover={webcamReady ? { scale: 1.08 } : undefined}
              whileTap={webcamReady ? { scale: 0.92 } : undefined}
              onClick={capturePhoto}
              disabled={!webcamReady}
              className={cn(
                "relative flex h-16 w-16 items-center justify-center rounded-full text-white shadow-glow-teal transition-opacity",
                webcamReady
                  ? "btn-glow"
                  : "bg-deep-200 cursor-not-allowed opacity-60",
              )}
            >
              <div className="absolute inset-[-3px] rounded-full border-[3px] border-white/20" />
              <Camera className="h-6 w-6" />
            </motion.button>
            <button
              onClick={stopWebcam}
              className="btn-ghost rounded-lg px-5 py-2.5 text-sm font-medium text-slate-400"
            >
              Cancel
            </button>
          </div>
          <p className="text-[11px] text-slate-600 mt-2">
            Position your face inside the outline, then tap capture
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "glass rounded-xl p-8 text-center cursor-pointer transition-all border-2 border-dashed",
              isDragOver
                ? "border-accent-300/50 bg-accent-50 shadow-glow-teal"
                : "border-[rgba(0,212,255,0.12)] hover:border-accent-300/30 hover:bg-accent-50"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              className="hidden"
            />
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-300/20 to-accent-500/10 border border-accent-300/10">
              <Upload className="h-6 w-6 text-accent-300" />
            </div>
            <p className="text-sm font-bold text-white mb-1">
              Drop your photo here
            </p>
            <p className="text-xs text-slate-500">
              or click to browse &middot; JPG, PNG
            </p>
          </div>

          <button
            onClick={startWebcam}
            className="glass rounded-xl p-8 text-center cursor-pointer transition-all border-2 border-dashed border-[rgba(0,212,255,0.12)] hover:border-accent-300/30 hover:bg-accent-50"
          >
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-500/20 to-accent-300/10 border border-accent-500/10">
              <Camera className="h-6 w-6 text-accent-400" />
            </div>
            <p className="text-sm font-bold text-white mb-1">
              Take a selfie
            </p>
            <p className="text-xs text-slate-500">
              Use your webcam or phone camera
            </p>
          </button>
        </div>
      )}
    </motion.div>
  );
}
