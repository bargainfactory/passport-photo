"use client";

import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload, Camera, Lightbulb, ArrowLeft, ArrowRight, X, RotateCcw, Square,
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
    // Resize large images to prevent huge base64 payloads and browser crashes
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
    // Guard against capturing before the camera has delivered a frame —
    // would otherwise produce a 0x0 / blank data URL.
    if (!vw || !vh) return;
    const canvas = document.createElement("canvas");
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    // Flip horizontally so the captured image is not mirrored
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

  const removeImage = () => {
    setImageUrl(null);
    setImageSource(null);
  };

  const retakeSelfie = () => {
    setImageUrl(null);
    setImageSource(null);
    startWebcam();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Back */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-navy-600 transition-colors mb-4"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Country
      </button>

      {/* Country badge */}
      <div className="inline-flex items-center gap-2 rounded-full bg-navy-600/5 border border-navy-600/10 px-3 py-1 text-sm font-semibold text-navy-600 mb-5">
        <span className="text-base">{country.flag}</span>
        {country.name} &mdash; {docType.charAt(0).toUpperCase() + docType.slice(1)} &mdash;{" "}
        {spec.width_mm}&times;{spec.height_mm}mm
      </div>

      {/* Tip cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        <div className="rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/60 p-4">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 flex-shrink-0">
              <Lightbulb className="h-4 w-4 text-amber-600" />
            </div>
            <div className="text-sm text-amber-900 leading-relaxed">
              <strong>Lighting tip:</strong> Face a window or soft lamp directly
              so light falls evenly across your face. Avoid side lighting,
              overhead lights, or direct flash &mdash; these create harsh
              shadows that often cause rejection.
            </div>
          </div>
        </div>
        <div className="rounded-xl bg-gradient-to-r from-sky-50 to-cyan-50 border border-sky-200/60 p-4">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-100 flex-shrink-0">
              <Square className="h-4 w-4 text-sky-600" />
            </div>
            <div className="text-sm text-sky-900 leading-relaxed">
              <strong>Background tip:</strong> Stand in front of a plain,
              single-color wall (white, cream, or light gray works best).
              A uniform background helps our AI cleanly separate you from the
              scene &mdash; cluttered or patterned backdrops can leave stray
              artifacts.
            </div>
          </div>
        </div>
      </div>

      {imageUrl ? (
        /* Image preview */
        <div className="glass rounded-xl p-6 shadow-glass text-center">
          <div className="relative inline-block">
            <img
              src={imageUrl}
              alt="Uploaded photo"
              className="rounded-lg max-h-80 mx-auto shadow-md"
            />
            <button
              onClick={removeImage}
              className="absolute -top-2 -right-2 flex h-7 w-7 items-center justify-center rounded-full bg-red-500 text-white shadow-md hover:bg-red-600 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Quick checklist */}
          <div className="mt-5 rounded-lg bg-slate-50 p-4 text-left max-w-md mx-auto">
            <p className="text-sm font-semibold text-navy-600 mb-2">
              Quick check before processing:
            </p>
            {[
              "Face clearly visible and front-facing",
              "Even lighting, no harsh shadows",
              "Neutral expression, eyes open",
              "Plain background (AI will replace it)",
            ].map((item) => (
              <div
                key={item}
                className="flex items-start gap-2 text-sm text-slate-600 py-0.5"
              >
                <span className="text-emerald-500 mt-0.5">&#10003;</span>
                {item}
              </div>
            ))}
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            {imageSource === "webcam" && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={retakeSelfie}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
              >
                <RotateCcw className="h-4 w-4" /> Retake
              </motion.button>
            )}
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onNext(imageUrl)}
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-navy-600 to-navy-500 px-8 py-3 text-sm font-bold text-white shadow-lg hover:shadow-xl transition-shadow"
            >
              Process Photo <ArrowRight className="h-4 w-4" />
            </motion.button>
          </div>
        </div>
      ) : showWebcam ? (
        /* Webcam with face guide overlay */
        <div className="glass rounded-xl p-6 shadow-glass text-center">
          <div className="relative inline-block mx-auto rounded-lg overflow-hidden bg-black"
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

            {/* Face guide overlay — appears after webcam loads */}
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

          {/* Capture controls */}
          <div className="flex items-center justify-center gap-4 mt-5">
            <motion.button
              whileHover={webcamReady ? { scale: 1.08 } : undefined}
              whileTap={webcamReady ? { scale: 0.92 } : undefined}
              onClick={capturePhoto}
              disabled={!webcamReady}
              className={cn(
                "relative flex h-16 w-16 items-center justify-center rounded-full text-white shadow-glow-teal transition-opacity",
                webcamReady
                  ? "bg-gradient-to-br from-teal-500 to-cyan-400"
                  : "bg-slate-300 cursor-not-allowed opacity-60",
              )}
            >
              <div className="absolute inset-[-3px] rounded-full border-[3px] border-white/30" />
              <Camera className="h-6 w-6" />
            </motion.button>
            <button
              onClick={stopWebcam}
              className="rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
          </div>

          <p className="text-xs text-slate-400 mt-3">
            Position your face inside the outline, then tap the capture button
          </p>
        </div>
      ) : (
        /* Upload zone */
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Drag & drop */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "glass rounded-xl p-8 text-center cursor-pointer transition-all border-2 border-dashed",
              isDragOver
                ? "border-teal-400 bg-teal-50/50 shadow-glow-teal"
                : "border-slate-200 hover:border-teal-300 hover:bg-teal-50/20"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              className="hidden"
            />
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-100 to-cyan-100">
              <Upload className="h-6 w-6 text-teal-600" />
            </div>
            <p className="text-sm font-bold text-navy-600 mb-1">
              Drag &amp; drop your photo
            </p>
            <p className="text-xs text-slate-400">
              or click to browse &middot; JPG, PNG
            </p>
          </div>

          {/* Webcam */}
          <button
            onClick={startWebcam}
            className="glass rounded-xl p-8 text-center cursor-pointer transition-all border-2 border-dashed border-slate-200 hover:border-teal-300 hover:bg-teal-50/20"
          >
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100">
              <Camera className="h-6 w-6 text-indigo-600" />
            </div>
            <p className="text-sm font-bold text-navy-600 mb-1">
              Take a selfie
            </p>
            <p className="text-xs text-slate-400">
              Use your webcam or phone camera
            </p>
          </button>
        </div>
      )}
    </motion.div>
  );
}
