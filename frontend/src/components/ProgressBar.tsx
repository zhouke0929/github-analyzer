"use client";

import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";

interface ProgressBarProps {
  currentStep: string;
  progress: number;
}

export function ProgressBar({ currentStep, progress }: ProgressBarProps) {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-3">
      <Progress value={progress} className="h-2" />
      <div className="flex items-center justify-center gap-2">
        <Loader2 className="w-4 h-4 text-github animate-spin" />
        <p className="text-sm text-muted-foreground">{currentStep}</p>
      </div>
    </div>
  );
}
