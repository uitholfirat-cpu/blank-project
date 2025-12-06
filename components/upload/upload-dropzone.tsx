"use client";

import { useCallback, useState } from "react";
import { CloudUpload, FolderOpen, FileArchive } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { useReport, type ReportData } from "@/components/report-context";
import { useSettings } from "@/components/settings/settings-context";

type PipelineStep =
  | "idle"
  | "uploading"
  | "extracting"
  | "tokenizing"
  | "analyzing"
  | "done";

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
  const router = useRouter();
  const { setReportData } = useReport();
  const { settings } = useSettings();

  const [isDragging, setIsDragging] = useState(false);
  const [stepIndex, setStepIndex] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadedSummary, setUploadedSummary] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeStep: PipelineStep =
    stepIndex === null
      ? "idle"
      : stepOrder[Math.min(stepIndex, stepOrder.length - 1)];

  const reset = useCallback(() => {
    setStepIndex(null);
    setProgress(0);
    setUploadedSummary(null);
    setError(null);
    setReportData(null);
  }, [setReportData]);

  const sendToBackend = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setError(null);

      console.log("[UploadDropzone] Starting upload pipeline", {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      });

      // Start pipeline at "uploading"
      setStepIndex(0);
      setProgress(10);

      const formData = new FormData();
      formData.append("file", file);

      const query = new URLSearchParams({
        threshold: String(settings.threshold),
        ignore_comments: settings.ignoreComments ? "true" : "false",
        ignore_variable_names: settings.ignoreVariableNames ? "true" : "false",
        sensitivity_mode: settings.sensitivityMode,
        ignore_function_names: settings.ignoreFunctionNames ? "true" : "false",
        ignore_type_names: settings.ignoreTypeNames ? "true" : "false",
        ignore_string_literals: settings.ignoreStringLiterals ? "true" : "false",
        ignore_numeric_literals: settings.ignoreNumericLiterals ? "true" : "false"
      });

      console.log("[UploadDropzone] Built query string", query.toString());

      const uploadUrl =
        process.env.NODE_ENV === "development"
          ? `http://localhost:8000/upload?${query.toString()}`
          : `/upload?${query.toString()}`;

      console.log("[UploadDropzone] Upload URL", uploadUrl);

      try {
        console.log("[UploadDropzone] Sending request to backend", {
          url: uploadUrl,
          time: new Date().toISOString()
        });

        const response = await fetch(uploadUrl, {
          method: "POST",
          body: formData
        });

        console.log("[UploadDropzone] Received response", {
          ok: response.ok,
          status: response.status
        });

        if (!response.ok) {
          let message = "Upload failed. Please check your ZIP file and try again.";
          try {
            const payload = (await response.json()) as {
              detail?: { message?: string } | string;
            };
            if (payload && typeof payload.detail === "object") {
              message = payload.detail.message ?? message;
            } else if (typeof payload.detail === "string") {
              message = payload.detail;
            }
          } catch {
            // Ignore JSON parsing errors and fall back to default message.
          }

          console.log("[UploadDropzone] Backend returned error response", {
            status: response.status,
            message
          });

          throw new Error(message);
        }

        // Move pipeline to "analyzing" while we parse and store data
        const analyzingIndex = stepOrder.indexOf("analyzing");
        if (analyzingIndex !== -1) {
          setStepIndex(analyzingIndex);
          setProgress(70);
        }

        console.log("[UploadDropzone] Response OK, parsing JSON");

        const data = (await response.json()) as ReportData;
        console.log("[UploadDropzone] Parsed report data", {
          plagiarismCases: Array.isArray(data.plagiarismCases)
            ? data.plagiarismCases.length
            : undefined
        });

        setReportData(data);

        // Mark as done and navigate to dashboard
        setStepIndex(stepOrder.length - 1);
        setProgress(100);

        console.log("[UploadDropzone] Upload and analysis completed, navigating to dashboard");
        router.push("/dashboard");
      } catch (err) {
        console.error("[UploadDropzone] Upload request failed", err);
        setStepIndex(null);
        setProgress(0);
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while running analysis."
        );
      } finally {
        console.log("[UploadDropzone] Upload pipeline finished");
        setIsUploading(false);
      }
    },
    [router, setReportData, settings]
  );

  const startPipeline = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const allFiles = Array.from(files);
      const zipFiles = allFiles.filter((f) =>
        f.name.toLowerCase().endsWith(".zip")
      );

      if (zipFiles.length === 0) {
        setError("Please upload at least one .zip file containing submissions.");
        return;
      }

      const zipCount = zipFiles.length;

      setUploadedSummary(
        `${allFiles.length} item${allFiles.length > 1 ? "s" : ""} selected • ` +
          `${zipCount} archive${zipCount === 1 ? "" : "s"} detected`
      );

      void sendToBackend(zipFiles[0]);
    },
    [sendToBackend]
  );

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

  return (
    <section className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-soft-card">
      <div className="relative flex flex-col gap-6 rounded-2xl bg-gradient-to-br from-background via-background to-muted/60 px-6 py-6 lg:flex-row lg:items-center lg:gap-8 lg:px-8 lg:py-8">
        <div className="flex-1 space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-100/70 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-emerald-800 shadow-sm dark:bg-emerald-500/10 dark:text-emerald-300">
            <CloudUpload className="h-3.5 w-3.5" />
            <span>Step 1 • Ingest submissions</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
            Drag in a lab folder or zipped submissions.
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            MasterGrader will unpack nested archives, normalize C code, and
            pre-compute similarity metrics for each question before you even
            open the dashboard.
          </p>
          {uploadedSummary && (
            <p className="text-xs text-emerald-700 dark:text-emerald-300/80">
              {uploadedSummary}
            </p>
          )}
          {isUploading && (
            <p className="text-xs text-sky-700 dark:text-sky-300">
              Running analysis...
            </p>
          )}
          {error && !isUploading && (
            <p className="text-xs text-destructive">
              {error}
            </p>
          )}
        </div>

        <div
          className={cn(
            "relative flex flex-1 flex-col gap-3 rounded-xl border border-border bg-background p-4 text-sm shadow-sm transition-colors dark:border-border dark:bg-card/90",
            isDragging &&
              "border-primary bg-muted/70 dark:border-primary dark:bg-muted/70"
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
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/15 text-sky-700 ring-1 ring-sky-500/40 dark:bg-sky-500/20 dark:text-sky-300">
                <FolderOpen className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                  Drop folder or .zip archives
                </p>
                <p className="text-xs text-muted-foreground">
                  Handles nested Moodle/Canvas exports and per-question zips.
                </p>
              </div>
            </div>
            <div className="hidden flex-col items-end gap-1 text-xs text-muted-foreground sm:flex">
              <span className="inline-flex items-center gap-1">
                <FileArchive className="h-3.5 w-3.5" />
                <span>.zip archives</span>
              </span>
              <span>Max 2GB per batch</span>
            </div>
          </div>

          <label
            htmlFor="upload-input"
            className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/40 px-4 py-6 text-center text-xs text-muted-foreground transition-colors hover:border-primary/70 hover:bg-muted/70 dark:border-border dark:bg-muted/60 dark:text-muted-foreground dark:hover:bg-muted/80"
          >
            <span className="font-medium text-foreground">
              Drop files here or click to browse
            </span>
            <span className="text-[0.7rem]">
              Upload your assignment root directory or one or more .zip files
              for Q1–Q6.
            </span>
            <input
              id="upload-input"
              type="file"
              multiple
              className="hidden"
              onChange={onInputChange}
              accept=".zip"
            />
          </label>

          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-[0.7rem] text-muted-foreground">
              <span className="font-semibold tracking-[0.16em] uppercase">
                Pipeline status
              </span>
              <span className="tabular-nums text-foreground">
                {Math.round(progress)}%
              </span>
            </div>
            <Progress value={progress} />
            <div className="mt-1 flex items-center justify-between text-[0.7rem] text-muted-foreground">
              <div className="flex gap-2">
                {stepOrder.map((step, index) => {
                  const reached =
                    stepIndex !== null && index <= (stepIndex ?? 0);
                  const isCurrent =
                    stepIndex !== null && index === (stepIndex ?? 0);
                  return (
                    <div
                      key={step}
                      className={cn(
                        "flex items-center gap-1.5",
                        index > 0 && "pl-2",
                        index > 0 && "border-l border-border dark:border-border"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-4 w-4 items-center justify-center rounded-full border border-border text-[0.6rem] text-muted-foreground",
                          reached &&
                            "border-sky-500 bg-sky-500/10 text-sky-900 dark:text-sky-100",
                          isCurrent &&
                            "animate-pulse border-sky-400 bg-sky-500/20 dark:bg-sky-500/30"
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
                <span className="text-[0.68rem] text-sky-700 dark:text-sky-300">
                  {stepLabel(activeStep)}
                </span>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-border pt-2 text-[0.7rem] text-muted-foreground dark:border-border">
            <span>Connected to your Python backend via FastAPI.</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="hidden border-border bg-background text-foreground hover:bg-muted/80 dark:border-border dark:bg-background dark:text-foreground dark:hover:bg-muted/80 sm:inline-flex"
              onClick={reset}
              disabled={isUploading}
            >
              Reset
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}