"use client";

import { useState, useMemo } from "react";
import { AnimatePresence } from "framer-motion";
import Header from "@/components/header";
import Stepper from "@/components/stepper";
import StepCountry from "@/components/step-country";
import StepUpload from "@/components/step-upload";
import StepPreview, { type ProcessedBundle } from "@/components/step-preview";
import StepDownload from "@/components/step-download";
import Footer from "@/components/footer";
import { type CountrySpec } from "@/lib/countries";
import { type Edits, type Variant, DEFAULT_EDITS } from "@/components/photo-editor";

function Particles() {
  const dots = useMemo(
    () =>
      Array.from({ length: 30 }, (_, i) => ({
        id: i,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        duration: `${12 + Math.random() * 20}s`,
        delay: `${Math.random() * 10}s`,
        driftX: `${(Math.random() - 0.5) * 80}px`,
        driftY: `${-30 - Math.random() * 60}px`,
        size: 1 + Math.random() * 2,
      })),
    [],
  );

  return (
    <div className="particles">
      {dots.map((d) => (
        <div
          key={d.id}
          className="particle"
          style={{
            left: d.left,
            top: d.top,
            width: d.size,
            height: d.size,
            "--duration": d.duration,
            "--delay": d.delay,
            "--drift-x": d.driftX,
            "--drift-y": d.driftY,
            animationDelay: d.delay,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

export default function Home() {
  const [step, setStep] = useState(0);
  const [country, setCountry] = useState<CountrySpec | null>(null);
  const [docType, setDocType] = useState<"passport" | "visa">("passport");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [bundle, setBundle] = useState<ProcessedBundle | null>(null);
  const [variant, setVariant] = useState<Variant>("enhanced");
  const [edits, setEdits] = useState<Edits>(DEFAULT_EDITS);
  const [editedOverrideUrl, setEditedOverrideUrl] = useState<string | null>(null);

  return (
    <div className="min-h-screen flex flex-col relative">
      <div className="bg-mesh" />
      <Particles />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Header />
        <Stepper currentStep={step} />

        <main className="flex-1 mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 pb-6">
          <AnimatePresence mode="wait">
            {step === 0 && (
              <StepCountry
                key="country"
                onNext={(c, dt) => {
                  setCountry(c);
                  setDocType(dt);
                  setStep(1);
                }}
              />
            )}

            {step === 1 && country && (
              <StepUpload
                key="upload"
                country={country}
                docType={docType}
                onNext={(url) => {
                  setImageUrl(url);
                  setStep(2);
                }}
                onBack={() => setStep(0)}
              />
            )}

            {step === 2 && country && imageUrl && (
              <StepPreview
                key="preview"
                country={country}
                docType={docType}
                imageUrl={imageUrl}
                variant={variant}
                onVariantChange={setVariant}
                edits={edits}
                onEditsChange={setEdits}
                editedOverrideUrl={editedOverrideUrl}
                onEditedOverrideChange={setEditedOverrideUrl}
                onNext={(b) => {
                  setBundle(b);
                  setStep(3);
                }}
                onBack={() => setStep(1)}
              />
            )}

            {step === 3 && country && bundle && (
              <StepDownload
                key="download"
                country={country}
                docType={docType}
                bundle={bundle}
                variant={variant}
                onVariantChange={setVariant}
                edits={edits}
                onEditsChange={setEdits}
                editedOverrideUrl={editedOverrideUrl}
                onEditedOverrideChange={setEditedOverrideUrl}
                onBack={() => setStep(2)}
              />
            )}
          </AnimatePresence>
        </main>

        <Footer />
      </div>
    </div>
  );
}
