"use client";

import * as React from "react";
import { useMemo, useState } from "react";
import { ArrowLeft, GitCompare, Sparkles } from "lucide-react";
// تغییر ۱: ایمپورت کردن Highlight و themes به صورت named import
import { Highlight, themes, type Language } from "prism-react-renderer";
import { useTheme } from "next-themes";

import { useSettings } from "@/components/settings/settings-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import type { PlagiarismCase } from "@/components/report-context";
import { cn } from "@/lib/utils";

type DiffViewerProps = {
  pair: PlagiarismCase;
  template: string;
  onBack?: () => void;
};

type LineMatchKind = "none" | "exact" | "structural";

type LineMeta = {
  isTemplate: boolean;
  matchKind: LineMatchKind;
};

type SideMeta = LineMeta[];

const cLanguage = "c" as Language;

export function DiffViewer({ pair, template, onBack }: DiffViewerProps) {
  const { settings } = useSettings();
  const { resolvedTheme } = useTheme();
  const [dimTemplate, setDimTemplate] = useState(true);
  const [highlightMatches, setHighlightMatches] = useState(true);

  // تغییر ۲: استفاده از آبجکت themes برای دسترسی به تم‌ها
  const theme = resolvedTheme === "light" ? themes.github : themes.nightOwl;

  const { leftMeta, rightMeta } = useMemo(
    () =>
      computeDiffMetadata(pair.codeA, pair.codeB, template, {
        ignoreComments: settings.ignoreComments,
        ignoreVariableNames: settings.ignoreVariableNames,
        functionSorting: settings.functionSorting
      }),
    [
      pair.codeA,
      pair.codeB,
      template,
      settings.ignoreComments,
      settings.ignoreVariableNames,
      settings.functionSorting
    ]
  );

  return (
    <section className="space-y-5">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          {onBack && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-0.5 hidden border-border/80 bg-background/80 text-xs md:inline-flex"
              onClick={onBack}
            >
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
              Back
            </Button>
          )}
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Diff viewer • {pair.questionId}
            </p>
            <h1 className="mt-1 text-lg font-semibold tracking-tight">
              {pair.studentA}{" "}
              <span className="text-xs text-muted-foreground">vs</span>{" "}
              {pair.studentB}
            </h1>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">
                <span className="mr-1 inline-flex items-center gap-1 text-[0.7rem]">
                  <GitCompare className="h-3.5 w-3.5" />
                  Similarity:
                </span>
                <span className="tabular-nums font-semibold text-foreground">
                  {pair.similarity.toFixed(1)}%
                </span>
              </Badge>
              <span className="text-[0.7rem]">
                Cluster <span className="font-medium">{pair.clusterId}</span> •
                threshold {settings.threshold}%
              </span>
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border/80 bg-card/90 px-3 py-2 text-xs">
          <div className="flex items-center gap-2">
            <Switch
              id="toggle-template"
              checked={dimTemplate}
              onCheckedChange={(v) => setDimTemplate(Boolean(v))}
            />
            <Label htmlFor="toggle-template" className="text-[0.7rem]">
              Dim professor template
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="toggle-matching"
              checked={highlightMatches}
              onCheckedChange={(v) => setHighlightMatches(Boolean(v))}
            />
            <Label htmlFor="toggle-matching" className="text-[0.7rem]">
              Highlight identical logic
            </Label>
          </div>
          <div className="flex items-center gap-2 text-[0.7rem] text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-sky-400" />
            <span>Respects similarity engine settings</span>
          </div>
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-3 text-[0.7rem] text-muted-foreground">
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-3 w-3 rounded-[3px] bg-emerald-500"
            aria-hidden="true"
          />
          <span>🟩 Exact copy (character-for-character)</span>
        </div>
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-3 w-3 rounded-[3px] bg-amber-400"
            aria-hidden="true"
          />
          <span>🟨 Renamed variables / whitespace (structural)</span>
        </div>
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-3 w-3 rounded-[3px] border border-border bg-background"
            aria-hidden="true"
          />
          <span>⬜ Original or unmatched code</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <CodePane
          title={`Student A – ${pair.studentA}`}
          code={pair.codeA}
          meta={leftMeta}
          template={template}
          dimTemplate={dimTemplate}
          highlightMatches={highlightMatches}
          theme={theme}
        />
        <CodePane
          title={`Student B – ${pair.studentB}`}
          code={pair.codeB}
          meta={rightMeta}
          template={template}
          dimTemplate={dimTemplate}
          highlightMatches={highlightMatches}
          theme={theme}
        />
      </div>
    </section>
  );
}

function CodePane({
  title,
  code,
  meta,
  template,
  dimTemplate,
  highlightMatches,
  theme
}: {
  title: string;
  code: string;
  meta: SideMeta;
  template: string;
  dimTemplate: boolean;
  highlightMatches: boolean;
  theme: any;
}) {
  const templateLines = template.split("\n").length;

  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-border/80 bg-card/95 shadow-soft-card">
      <header className="flex items-center justify-between border-b border-border/80 px-3 py-2 text-xs">
        <div className="flex flex-col">
          <span className="font-semibold">{title}</span>
          <span className="text-[0.7rem] text-muted-foreground">
            Lines of code: {code.split("\n").length} • template baseline:{" "}
            {templateLines} lines
          </span>
        </div>
      </header>
      <div className="relative max-h-[520px] overflow-auto bg-muted/30">
        {/* تغییر ۳: حذف {...defaultProps} */}
        <Highlight theme={theme} code={code} language={cLanguage}>
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre
              className={cn(
                className,
                "m-0 min-h-full w-full bg-transparent p-3 text-[11px] leading-relaxed"
              )}
              style={style}
            >
              {tokens.map((line, i) => {
                const lineMeta =
                  meta[i] ??
                  ({
                    isTemplate: false,
                    matchKind: "none"
                  } as LineMeta);

                const isTemplateLine = lineMeta.isTemplate;
                const matchKind = lineMeta.matchKind ?? "none";
                const isExactMatch = matchKind === "exact";
                const isStructuralMatch = matchKind === "structural";
                const hasMatch = isExactMatch || isStructuralMatch;

                return (
                  <div
                    key={i}
                    {...getLineProps({ line, key: i })}
                    className={cn(
                      "flex border-l-2 border-transparent px-2 py-[1px]",
                      isTemplateLine && dimTemplate && "opacity-60 bg-muted/40",
                      highlightMatches &&
                        isExactMatch &&
                        "border-emerald-500/70 bg-emerald-500/10",
                      highlightMatches &&
                        isStructuralMatch &&
                        "border-amber-500/70 bg-amber-500/10",
                      !isTemplateLine && !hasMatch && "hover:bg-muted/40"
                    )}
                  >
                    <span className="mr-3 w-10 select-none text-right text-[0.65rem] text-muted-foreground">
                      {i + 1}
                    </span>
                    <span className="flex-1 whitespace-pre">
                      {line.map((token, key) => (
                        <span
                          key={key}
                          {...getTokenProps({ token, key })}
                          className={cn(
                            "transition-colors",
                            highlightMatches &&
                              isExactMatch &&
                              "text-emerald-800 dark:text-emerald-200",
                            highlightMatches &&
                              isStructuralMatch &&
                              "text-amber-800 dark:text-amber-200",
                            isTemplateLine &&
                              dimTemplate &&
                              "text-muted-foreground"
                          )}
                        />
                      ))}
                    </span>
                  </div>
                );
              })}
            </pre>
          )}
        </Highlight>
      </div>
    </div>
  );
}

function computeDiffMetadata(
  codeA: string,
  codeB: string,
  template: string,
  opts: {
    ignoreComments: boolean;
    ignoreVariableNames: boolean;
    functionSorting: boolean;
  }
): { leftMeta: SideMeta; rightMeta: SideMeta } {
  const templateLines = new Set(
    template
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0)
  );

  const linesA = codeA.split("\n");
  const linesB = codeB.split("\n");

  const rawSetA = new Set(linesA.filter((line) => line.trim().length > 0));
  const rawSetB = new Set(linesB.filter((line) => line.trim().length > 0));

  const normalizedLinesA = linesA.map((line) => normalizeLine(line, opts));
  const normalizedLinesB = linesB.map((line) => normalizeLine(line, opts));

  const normalizedSetA = new Set(
    normalizedLinesA.filter((line) => line.length > 0)
  );
  const normalizedSetB = new Set(
    normalizedLinesB.filter((line) => line.length > 0)
  );

  const leftMeta: SideMeta = linesA.map((line, index) => {
    const trimmed = line.trim();
    const isTemplate = trimmed.length > 0 && templateLines.has(trimmed);

    let matchKind: LineMatchKind = "none";

    if (!isTemplate && trimmed.length > 0) {
      if (rawSetB.has(line)) {
        matchKind = "exact";
      } else {
        const normalized = normalizedLinesA[index];
        if (normalized.length > 0 && normalizedSetB.has(normalized)) {
          matchKind = "structural";
        }
      }
    }

    return { isTemplate, matchKind };
  });

  const rightMeta: SideMeta = linesB.map((line, index) => {
    const trimmed = line.trim();
    const isTemplate = trimmed.length > 0 && templateLines.has(trimmed);

    let matchKind: LineMatchKind = "none";

    if (!isTemplate && trimmed.length > 0) {
      if (rawSetA.has(line)) {
        matchKind = "exact";
      } else {
        const normalized = normalizedLinesB[index];
        if (normalized.length > 0 && normalizedSetA.has(normalized)) {
          matchKind = "structural";
        }
      }
    }

    return { isTemplate, matchKind };
  });

  return { leftMeta, rightMeta };
}

function normalizeLine(
  line: string,
  opts: {
    ignoreComments: boolean;
    ignoreVariableNames: boolean;
    functionSorting: boolean;
  }
): string {
  let trimmed = line.trim();

  if (opts.ignoreComments) {
    if (
      trimmed.startsWith("//") ||
      trimmed.startsWith("/*") ||
      trimmed.startsWith("*")
    ) {
      return "";
    }
  }

  if (opts.ignoreVariableNames) {
    trimmed = trimmed.replace(
      /\b[a-zA-Z_][a-zA-Z0-9_]*\b/g,
      (match) => {
        if (
          [
            "int",
            "float",
            "double",
            "char",
            "void",
            "return",
            "if",
            "else",
            "for",
            "while",
            "do",
            "switch",
            "case",
            "break",
            "continue",
            "scanf",
            "printf",
            "main"
          ].includes(match)
        ) {
          return match;
        }
        return "id";
      }
    );
  }

  // For demonstration, we do not re-order functions (that would require a parser),
  // but we keep the flag here to show where such logic would plug in.
  if (opts.functionSorting) {
    // no-op in mock UI
  }

  return trimmed.replace(/\s+/g, " ");
}
