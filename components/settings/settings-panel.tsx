"use client";

import { useState } from "react";
import { FileText, SlidersHorizontal } from "lucide-react";

import { useSettings } from "@/components/settings/settings-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";

export function SettingsPanel() {
  const { settings, setSettings } = useSettings();
  const [templateFileName, setTemplateFileName] = useState<string | null>(null);

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
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  ignoreComments: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="ignore-vars"
              label="Ignore variable names"
              description="Tokenize identifiers so renaming alone does not evade detection."
              checked={settings.ignoreVariableNames}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  ignoreVariableNames: Boolean(value)
                }))
              }
            />
            <ToggleRow
              id="function-sorting"
              label="Function sorting"
              description="Compare functions independent of their order (advanced)."
              checked={settings.functionSorting}
              onCheckedChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
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
        </CardContent>
      </Card>
    </section>
  );
}

function ToggleRow({
  id,
  label,
  description,
  checked,
  onCheckedChange
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
}) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-1 flex-col gap-1.5">
        <div className="flex items-center justify-between gap-2">
          <Label htmlFor={id} className="text-xs">
            {label}
          </Label>
          <Switch
            id={id}
            checked={checked}
            onCheckedChange={(value) => onCheckedChange(Boolean(value))}
          />
        </div>
        <p className="text-[0.68rem] text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}