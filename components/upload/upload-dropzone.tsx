"use client";

import { useCallback, useEffect, useState } from "react";
import { CloudUpload, FolderOpen, FileArchive } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

type PipelineStep = "idle" | "uploading" | "extracting" | "tokenizing" | "analyzing" | "done";

const stepOrder: PipelineStep[] = [
  "uploading",
  "extracting",
  "tokenizing",
  "analyzing",
  "done"
];

function stepLabel(step: PipelineStep) {
  switch (step) {
    case "uploading":
      return "Uploading submissions";
    case "extracting":
      return "Extracting archives";
    case "tokenizing":
      return "Tokenizing C code";
    case "analyzing":
      return "Running similarity engine";
    case "done":
      return "Ready – view dashboard";
    default:
      return "Idle";
  }
}

export function UploadDropzone() {
  const [isDragging, setIsDragging] = useState(false);
  const [stepIndex, setStepIndex] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadedSummary, setUploadedSummary] = useState<string | null>(null);

  const activeStep: PipelineStep =
    stepIndex === null ? "idle" : stepOrder[Math.min(stepIndex, stepOrder.length - 1)];

  const reset = useCallback(() => {
    setStepIndex(null);
    setProgress(0);
  }, []);

  const startPipeline = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const zipCount = Array.from(files).filter((f) =>
      f.name.toLowerCase().endsWith(".zip")
    ).length;

    setUploadedSummary(
      `${files.length} item${files.length > 1 ? "s" : ""} uploaded • ` +
        `${zipCount} archive${zipCount === 1 ? "" : "s"} detected`
    );

    setStepIndex(0);
    setProgress(4);
  }, []);

  useEffect(() => {
    if (stepIndex === null) return;
    if (stepIndex >= stepOrder.length - 1) {
      setProgress(100);
      return;
    }

    const stepDuration = 900 + stepIndex * 300;

    const interval = window.setInterval(() => {
      setProgress((prev) => Math.min(prev + 10, 96));
    }, stepDuration / 8);

    const timeout = window.setTimeout(() => {
      setStepIndex((prev) => (prev === null ? null : prev + 1));
    }, stepDuration);

    return () => {
      window.clearInterval(interval);
      window.clearTimeout(timeout);
    };
  }, [stepIndex]);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const files = e.dataTransfer.files;
      reset();
      startPipeline(files);
    },
    [reset, startPipeline]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      reset();
      startPipeline(files);
    },
    [reset, startPipeline]
  );

  const stepProgress =
    activeStep === "idle"
      ? 0
      : activeStep === "done"
      ? 100
      : ((stepIndex ?? 0) / (stepOrder.length - 1)) * 100;

  return (
    <section className="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900 p-[1px] shadow-soft-card">
      <div className="relative flex flex-col gap-6 rounded-2xl bg-gradient-to-br from-slate-950/80 via-slate-950 to-slate-950/90 px-6 py-6 lg:flex-row lg:items-center lg:gap-8 lg:px-8 lg:py-8">
        <div className="flex-1 space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-emerald-300">
            <CloudUpload className="h-3.5 w-3.5" />
            <span>Step 1 • Ingest submissions</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
            Drag in a lab folder or zipped submissions.
          </h1>
          <p className="max-w-xl text-sm text-slate-300">
            MasterGrader will unpack nested archives, normalize C code, and pre-compute
            similarity metrics for each question before you even open the dashboard.
          </p>
          {uploadedSummary && (
            <p className="text-xs text-emerald-300/80">{uploadedSummary}</p>
          )}
        </div>

        <div
          className={cn(
            "relative flex flex-1 flex-col gap-3 rounded-xl border border-sky-500/40 bg-slate-900/80 p-4 text-sm shadow-lg transition-colors",
            isDragging && "border-sky-400 bg-slate-900/60"
          )}
          onDragOver={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);
          }}
          onDrop={onDrop}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/20 text-sky-300 ring-1 ring-sky-500/40">
                <FolderOpen className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                  Drop folder or .zip archives
                </p>
                <p className="text-xs text-slate-400">
                  Handles nested Moodle/Canvas exports and per-question zips.
                </p>
              </div>
            </div>
            <div className="hidden flex-col items-end gap-1 text-xs text-slate-400 sm:flex">
              <span className="inline-flex items-center gap-1">
                <FileArchive className="h-3.5 w-3.5" />
                <span>.zip, .tar.gz, raw folders</span>
              </span>
              <span>Max 2GB per batch (demo)</span>
            </div>
          </div>

          <label
            htmlFor="upload-input"
            className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-700/80 bg-slate-950/50 px-4 py-6 text-center text-xs text-slate-400 transition-colors hover:border-sky-500/70 hover:bg-slate-900/70"
          >
            <span className="font-medium text-slate-200">
              Drop files here or click to browse
            </span>
            <span className="text-[0.7rem]">
              Upload your assignment root directory or multiple .zip files for Q1–Q6.
            </span>
            <input
              id="upload-input"
              type="file"
              multiple
              className="hidden"
              onChange={onInputChange}
            />
          </label>

          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-[0.7rem] text-slate-400">
              <span className="font-semibold tracking-[0.16em] uppercase">
                Pipeline status
              </span>
              <span className="tabular-nums text-slate-300">
                {Math.round(progress)}%
              </span>
            </div>
            <Progress value={progress} />
            <div className="mt-1 flex items-center justify-between text-[0.7rem] text-slate-400">
              <div className="flex gap-2">
                {stepOrder.map((step, index) => {
                  const reached = stepIndex !== null && index <= (stepIndex ?? 0);
                  const isCurrent = stepIndex !== null && index === (stepIndex ?? 0);
                  return (
                    <div
                      key={step}
                      className={cn(
                        "flex items-center gap-1.5",
                        index > 0 && "pl-2",
                        index > 0 && "border-l border-slate-700/80"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-4 w-4 items-center justify-center rounded-full border border-slate-600/80 text-[0.6rem]",
                          reached && "border-sky-500 bg-sky-500/20 text-sky-100",
                          isCurrent && "animate-pulse border-sky-400 bg-sky-500/30"
                        )}
                      >
                        {index + 1}
                      </span>
                      <span className="hidden text-[0.68rem] sm:inline">
                        {stepLabel(step)}
                      </span>
                    </div>
                  );
                })}
              </div>
              {activeStep !== "idle" && (
                <span className="text-[0.68rem] text-sky-300">
                  {stepLabel(activeStep)}
                </span>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[0.7rem] text-slate-500">
            <span>Mock pipeline – integrates with your Python backend via API.</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="hidden border-slate-700/80 bg-slate-900/80 text-slate-200 hover:bg-slate-800/80 sm:inline-flex"
              onClick={reset}
            >
              Reset demo
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}