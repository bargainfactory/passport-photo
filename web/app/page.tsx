"use client";

import { useState } from "react";
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

export default function Home() {
  const [step, setStep] = useState(0);
  const [country, setCountry] = useState<CountrySpec | null>(null);
  const [docType, setDocType] = useState<"passport" | "visa">("passport");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [bundle, setBundle] = useState<ProcessedBundle | null>(null);
  const [variant, setVariant] = useState<Variant>("enhanced");
  const [edits, setEdits] = useState<Edits>(DEFAULT_EDITS);
  // Advanced-tools override: when the user applies magnify/erase/fill
  // edits, we stash the resulting data URL here and prefer it over the
  // bundle's original URL for both on-screen display and download.
  const [editedOverrideUrl, setEditedOverrideUrl] = useState<string | null>(null);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <Stepper currentStep={step} />

      <main className="flex-1 mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 pb-8">
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
  );
}
