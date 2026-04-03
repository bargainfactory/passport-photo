"use client";

import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import Header from "@/components/header";
import Stepper from "@/components/stepper";
import StepCountry from "@/components/step-country";
import StepUpload from "@/components/step-upload";
import StepPreview from "@/components/step-preview";
import StepDownload from "@/components/step-download";
import Footer from "@/components/footer";
import { type CountrySpec } from "@/lib/countries";

export default function Home() {
  const [step, setStep] = useState(0);
  const [country, setCountry] = useState<CountrySpec | null>(null);
  const [docType, setDocType] = useState<"passport" | "visa">("passport");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [sheetUrl, setSheetUrl] = useState<string | null>(null);

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
              onNext={(pUrl, sUrl) => {
                setProcessedUrl(pUrl);
                setSheetUrl(sUrl);
                setStep(3);
              }}
              onBack={() => setStep(1)}
            />
          )}

          {step === 3 && country && processedUrl && sheetUrl && (
            <StepDownload
              key="download"
              country={country}
              docType={docType}
              processedUrl={processedUrl}
              sheetUrl={sheetUrl}
              onBack={() => setStep(2)}
            />
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}
