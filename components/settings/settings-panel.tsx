"use client";

import { useState } from "react";
import { FileText, SlidersHorizontal } from "lucide-react";

import {
  useSettings,
  type EngineSettings
} from "@/components/settings/settings-context";
import { useReport } from "@/components/report-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type SensitivityMode = EngineSettings["sensitivityMode"];

export function SettingsPanel() {
  const { settings, setSettings } = useSettings();
  const { setReportData } = useReport();
  const [templateFileName, setTemplateFileName] = useState<string | null>(null);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  const currentMode: SensitivityMode = settings.sensitivityMode;
  const isCustomMode = currentMode === "custom";

  const handleModeChange = (mode: SensitivityMode) => {
    setSettings((prev) => {
      if (prev.sensitivityMode === mode) {
        return prev;
      }

      const base: EngineSettings = { ...prev, sensitivityMode: mode };

      switch (mode) {
        case "smart":
          return {
            ...base,
            ignoreComments: true,
            ignoreVariableNames: true,
            ignoreFunctionNames: true,
            ignoreTypeNames: true,
            ignoreStringLiterals: true,
            ignoreNumericLiterals: true,
            functionSorting: true
          };
        case "strict":
          return {
            ...base,
            ignoreComments: false,
            ignoreVariableNames: false,
            ignoreFunctionNames: false,
            ignoreTypeNames: false,
            ignoreStringLiterals: false,
            ignoreNumericLiterals: false,
            functionSorting: false
          };
        case "balanced":
          return {
            ...base,
            ignoreComments: true,
            ignoreVariableNames: true,
            ignoreFunctionNames: false,
            ignoreTypeNames: false,
            ignoreStringLiterals: true,
            ignoreNumericLiterals: true,
            functionSorting: false
          };
        case "custom":
        default:
          return base;
      }
    });
  };

  const modeSubtitle =
    currentMode === "smart"
      ? "Aggressive structural matching"
      : currentMode === "strict"
      ? "Only flags near-exact copies"
      : currentMode === "custom"
      ? "Manual sensitivity configuration"
      : "Balanced defaults (recommended)";

  const handleReanalyze = async () => {
    setStatusMessage(null);
    setStatusError(null);
    setIsReanalyzing(true);

    const payload = {
      threshold: settings.threshold,
      ignore_comments: settings.ignoreComments,
      ignore_variable_names: settings.ignoreVariableNames,
      normalize_whitespace: undefined,
      tokenization_enabled: undefined,
      sensitivity_mode: settings.sensitivityMode,
      ignore_function_names: settings.ignoreFunctionNames,
      ignore_type_names: settings.ignoreTypeNames,
      ignore_string_literals: settings.ignoreStringLiterals,
      ignore_numeric_literals: settings.ignoreNumericLiterals,
    };

    const reanalyzeUrl =
      process.env.NODE_ENV === "development"
        ? "http://localhost:8000/reanalyze"
        : "/reanalyze";

    try {
      const response = await fetch(reanalyzeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let message = "Re-analysis failed. Please upload a ZIP file first.";
        try {
          const json = (await response.json()) as {
            detail?: { message?: string } | string;
          };
          if (json && typeof json.detail === "object") {
            message = json.detail.message ?? message;
          } else if (typeof json.detail === "string") {
            message = json.detail;
          }
        } catch {
          // Ignore JSON parsing issues and fall back to default.
        }
        throw new Error(message);
      }

      const data = (await response.json()) as import("@/components/report-context").ReportData;
      setReportData(data);
      setStatusMessage("Analysis updated!");
    } catch (err) {
      setStatusError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred while updating analysis.",
      );
    } finally {
      setIsReanalyzing(false);
    }
  };

  return (
    <section className="grid gap-4 lg:grid-cols-[minmax(0,_1.6fr)_minmax(0,_1.1fr)]">
      <Card className="border-border/80 bg-card/90">
        <CardHeader className="flex items-center justify-between gap-2">
          <div>
            <CardTitle className="text-sm font-semibold tracking-tight">
              Similarity thresholds
            </CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Control how aggressively MasterGrader flags suspicious C submissions.
            </p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-500/10 text-sky-400 ring-1 ring-sky-500/40">
            <SlidersHorizontal className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <Label className="text-xs">Detection mode</Label>
              <span className="text-[0.7rem] text-muted-foreground">
                {modeSubtitle}
              </span>
            </div>
            <div className="grid gap-2 sm:grid-cols-4">
              <ModeButton
                mode="smart"
                label="Smart"
                description="Ignore most cosmetic changes to surface hidden collusion."
                active={currentMode === "smart"}
                onClick={handleModeChange}
              />
              <ModeButton
                mode="balanced"
                label="Balanced"
                description="Recommended defaults for most C lab cohorts."
                active={currentMode === "balanced"}
                onClick={handleModeChange}
              />
              <ModeButton
                mode="strict"
                label="Strict"
                description="Only flag near-identical submissions."
                active={currentMode === "strict"}
                onClick={handleModeChange}
              />
              <ModeButton
                mode="custom"
                label="Custom"
                description="Manually tune what the engine should ignore."
                active={currentMode === "custom"}
                onClick={handleModeChange}
              />
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <Label htmlFor="threshold-slider" className="text-xs">
                High‑risk threshold
              </Label>
              <span className="tabular-nums text-[0.75rem] text-muted-foreground">
                {settings.threshold.toFixed(0)}%
              </span>
            </div>
            <Slider
              id="threshold-slider"
              min={40}
              max={100}
              step={1}
              value={[settings.threshold]}
              onValueChange={([value]) =>
                setSettings((prev) => ({ ...prev, threshold: value }))
              }
            />
            <p className="text-[0.7rem] text-muted-foreground">
              Pairs above this similarity are marked as{" "}
              <span className="font-medium text-red-400">high risk</span> in the
              table and network graph.
            </p>
          </div>

          <div className="grid gap-3 text-xs md:grid-cols-2">
            <ToggleRow
              id="ignore-comments"
              label="Ignore comments"
              description="Strip // and /* */ blocks before computing similarity."
              checked={settings.ignoreComments}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreComments: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-vars"
              label="Ignore variable names"
              description="Tokenize identifiers so renaming alone does not evade detection."
              checked={settings.ignoreVariableNames}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreVariableNames: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-func-names"
              label="Ignore function names"
              description="Treat renamed helper functions as equivalent when comparing logic."
              checked={settings.ignoreFunctionNames}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreFunctionNames: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-type-names"
              label="Ignore type names"
              description="Ignore renamed structs, enums, and typedefs when matching."
              checked={settings.ignoreTypeNames}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreTypeNames: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-strings"
              label="Ignore string literals"
              description="Normalize string contents so only control flow and structure matter."
              checked={settings.ignoreStringLiterals}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreStringLiterals: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-numbers"
              label="Ignore numbers"
              description="Treat numeric constants as generic tokens during comparison."
              checked={settings.ignoreNumericLiterals}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  ignoreNumericLiterals: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="function-sorting"
              label="Function sorting"
              description="Compare functions independent of their order (advanced)."
              checked={settings.functionSorting}
              disabled={!isCustomMode}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  sensitivityMode: "custom",
                  functionSorting: Boolean(value)
                }))
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/80 bg-card/90">
        <CardHeader>
          <CardTitle className="text-sm font-semibold tracking-tight">
            Professor template
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <p className="text-muted-foreground">
            Upload the base C file you provide to students (e.g. includes,{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-[0.7rem]">
              main()
            </code>{" "}
            skeleton, helper stubs). Matching lines will be dimmed in the diff viewer
            so you can focus on student-authored logic.
          </p>
          <div className="space-y-2">
            <Label htmlFor="template-file">Professor base code</Label>
            <div className="flex items-center gap-3">
              <div className="flex flex-1 items-center gap-2 rounded-md border border-dashed border-border/80 bg-background/80 px-3 py-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div className="flex flex-col">
                  <span className="text-[0.75rem] font-medium">
                    {templateFileName ?? "No file selected"}
                  </span>
                  <span className="text-[0.65rem] text-muted-foreground">
                    .c or .h files • used only for boilerplate dimming in this demo
                  </span>
                </div>
              </div>
              <label
                htmlFor="template-file"
                className="inline-flex cursor-pointer items-center rounded-md border border-border/80 bg-background px-3 py-1.5 text-[0.75rem] font-medium text-foreground shadow-sm hover:bg-muted/80"
              >
                Browse
              </label>
              <Input
                id="template-file"
                type="file"
                accept=".c,.h"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  setTemplateFileName(file?.name ?? null);
                }}
              />
            </div>
          </div>
          <p className="text-[0.68rem] text-muted-foreground">
            In production, this configuration would be persisted and passed to your
            Python backend so the same template is excluded from similarity across
            all questions.
          </p>
          <div className="flex items-center justify-between pt-2 text-[0.7rem]">
            <button
              type="button"
              onClick={handleReanalyze}
              disabled={isReanalyzing}
              className="inline-flex items-center rounded-md border border-border/80 bg-background px-3 py-1.5 text-[0.75rem] font-medium text-foreground shadow-sm hover:bg-muted/80 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isReanalyzing ? "Re-analyzing…" : "Save &amp; Re-analyze"}
            </button>
            <div className="min-h-[1.25rem] text-right">
              {statusMessage && (
                <span className="text-[0.7rem] font-medium text-emerald-600 dark:text-emerald-300">
                  {statusMessage}
                </span>
              )}
              {statusError && (
                <span className="text-[0.7rem] font-medium text-destructive">
                  {statusError}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

type ModeButtonProps = {
  mode: SensitivityMode;
  label: string;
  description: string;
  active: boolean;
  onClick: (mode: SensitivityMode) => void;
};

function ModeButton({
  mode,
  label,
  description,
  active,
  onClick
}: ModeButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "flex flex-col items-start rounded-md border px-3 py-2 text-left text-[0.7rem] transition-colors",
        active
          ? "border-primary bg-primary/10 text-foreground"
          : "border-border/70 bg-background/80 text-muted-foreground hover:bg-muted/60"
      )}
      onClick={() => onClick(mode)}
    >
      <span className="text-xs font-medium text-foreground">{label}</span>
      <span className="mt-0.5 leading-snug">{description}</span>
    </button>
  );
}

function ToggleRow({
  id,
  label,
  description,
  checked,
  disabled,
  onCheckedChange
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (value: boolean) => void;
}) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-1 flex-col gap-1.5">
        <div className="flex items-center justify-between gap-2">
          <Label
            htmlFor={id}
            className={cn(
              "text-xs",
              disabled && "text-muted-foreground/70 cursor-not-allowed"
            )}
          >
            {label}
          </Label>
          <Switch
            id={id}
            checked={checked}
            disabled={disabled}
            onCheckedChange={(value) => {
              if (!disabled) {
                onCheckedChange(Boolean(value));
              }
            }}
          />
        </div>
        <p
          className={cn(
            "text-[0.68rem] text-muted-foreground",
            disabled && "opacity-60"
          )}
        >
          {description}
        </p>
      </div>
    </div>
  );
}