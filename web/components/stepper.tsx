"use client";

import { Globe, Upload, Eye, Download, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface StepperProps {
  currentStep: number;
}

const STEPS = [
  { label: "Country", icon: Globe },
  { label: "Upload", icon: Upload },
  { label: "Preview", icon: Eye },
  { label: "Download", icon: Download },
];

export default function Stepper({ currentStep }: StepperProps) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <div className="flex items-center justify-between">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const isDone = i < currentStep;
          const isActive = i === currentStep;
          const isTodo = i > currentStep;

          return (
            <div key={step.label} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div className="flex flex-col items-center gap-1.5">
                <motion.div
                  initial={false}
                  animate={{
                    scale: isActive ? 1 : 0.9,
                    boxShadow: isActive
                      ? "0 0 20px rgba(0, 212, 255, 0.4)"
                      : "0 0 0px rgba(0, 212, 255, 0)",
                  }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full transition-colors duration-300",
                    isDone && "bg-emerald-500 text-white",
                    isActive && "bg-gradient-to-br from-teal-500 to-cyan-400 text-white",
                    isTodo && "bg-slate-100 text-slate-400 border border-slate-200"
                  )}
                >
                  {isDone ? (
                    <Check className="h-[18px] w-[18px]" strokeWidth={3} />
                  ) : (
                    <Icon className="h-[18px] w-[18px]" />
                  )}
                </motion.div>
                <span
                  className={cn(
                    "text-xs font-semibold transition-colors duration-300",
                    isDone && "text-emerald-600",
                    isActive && "text-navy-600",
                    isTodo && "text-slate-400"
                  )}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {i < STEPS.length - 1 && (
                <div className="flex-1 mx-2 mt-[-18px]">
                  <div className="h-[2px] w-full rounded-full bg-slate-200 overflow-hidden">
                    <motion.div
                      initial={{ width: "0%" }}
                      animate={{
                        width: isDone ? "100%" : isActive ? "50%" : "0%",
                      }}
                      transition={{ duration: 0.5, ease: "easeInOut" }}
                      className={cn(
                        "h-full rounded-full",
                        isDone
                          ? "bg-emerald-500"
                          : "bg-gradient-to-r from-emerald-500 to-teal-400"
                      )}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
