"use client";

import * as React from "react";
import { useMemo, useState } from "react";
import { ArrowLeft, GitCompare, Sparkles } from "lucide-react";
import { diffLines, diffWords, type Change } from "diff";

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

type RowKind = "exact" | "structural" | "left-only" | "right-only" | "mismatch";

type TokenKind = "unchanged" | "added" | "removed";

type DiffToken = {
  value: string;
  kind: TokenKind;
};

type DiffCell = {
  lineNumber: number | null;
  text: string;
  tokens: DiffToken[];
  isTemplate: boolean;
};

type DiffRow = {
  left: DiffCell | null;
  right: DiffCell | null;
  kind: RowKind;
};

export function DiffViewer({ pair, template, onBack }: DiffViewerProps) {
  const { settings } = useSettings();
  const [dimTemplate, setDimTemplate] = useState(true);
  const [highlightMatches, setHighlightMatches] = useState(true);

  const rows = useMemo(
    () =>
      buildDiffRows(pair.codeA, pair.codeB, template, {
        ignoreComments: settings.ignoreComments,
        ignoreVariableNames: settings.ignoreVariableNames,
        functionSorting: settings.functionSorting,
      }),
    [
      pair.codeA,
      pair.codeB,
      template,
      settings.ignoreComments,
      settings.ignoreVariableNames,
      settings.functionSorting,
    ],
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
          <span>🟩 Exact match (character-for-character)</span>
        </div>
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-3 w-3 rounded-[3px] bg-amber-400"
            aria-hidden="true"
          />
          <span>🟨 Structural match (renamed variables, formatting-only changes)</span>
        </div>
        <div className="inline-flex items-center gap-1.5">
          <span
            className="inline-flex h-3 w-3 rounded-[3px] bg-red-500"
            aria-hidden="true"
          />
          <span
            className="inline-flex h-3 w-3 rounded-[3px] bg-emerald-500"
            aria-hidden="true"
          />
          <span>🟥/🟩 Content mismatch (removed / added code)</span>
        </div>
      </div>

      <div className="flex flex-col overflow-hidden rounded-xl border border-border/80 bg-card/95 shadow-soft-card">
        <header className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] border-b border-border/80 text-[0.7rem]">
          <div className="px-3 py-2 font-semibold">
            Student A &ndash; {pair.studentA}
          </div>
          <div className="flex items-center justify-center px-2 py-2 text-muted-foreground">
            Lines
          </div>
          <div className="px-3 py-2 text-right font-semibold">
            Student B &ndash; {pair.studentB}
          </div>
        </header>
        <div className="max-h-[520px] overflow-auto bg-muted/30 text-[11px] font-mono allow-select">
          {rows.map((row, index) => (
            <div
              key={index}
              className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] border-b border-border/40 last:border-b-0"
            >
              <DiffCellView
                side="left"
                rowKind={row.kind}
                cell={row.left}
                dimTemplate={dimTemplate}
                highlightMatches={highlightMatches}
              />
              <div className="flex flex-col items-center justify-center px-2 py-[1px] text-[0.65rem] text-muted-foreground">
                <span className="tabular-nums">
                  {row.left?.lineNumber ?? ""}
                </span>
                <span className="tabular-nums">
                  {row.right?.lineNumber ?? ""}
                </span>
              </div>
              <DiffCellView
                side="right"
                rowKind={row.kind}
                cell={row.right}
                dimTemplate={dimTemplate}
                highlightMatches={highlightMatches}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DiffCellView({
  side,
  rowKind,
  cell,
  dimTemplate,
  highlightMatches,
}: {
  side: "left" | "right";
  rowKind: RowKind;
  cell: DiffCell | null;
  dimTemplate: boolean;
  highlightMatches: boolean;
}) {
  const isTemplate = cell?.isTemplate ?? false;

  const baseClasses =
    "relative flex min-h-[1.1rem] items-stretch whitespace-pre-wrap break-words px-3 py-[1px]";

  const classes = cn(
    baseClasses,
    !cell && "bg-muted/20",
    cell &&
      isTemplate &&
      dimTemplate &&
      "bg-muted/40 text-muted-foreground",
    cell &&
      highlightMatches &&
      rowKind === "exact" &&
      "bg-emerald-500/10 border-l-2 border-emerald-500/70",
    cell &&
      highlightMatches &&
      rowKind === "structural" &&
      "bg-amber-500/10 border-l-2 border-amber-500/70",
    cell &&
      !isTemplate &&
      rowKind === "left-only" &&
      side === "left" &&
      "bg-red-500/10 border-l-2 border-red-500/70",
    cell &&
      !isTemplate &&
      rowKind === "right-only" &&
      side === "right" &&
      "bg-emerald-500/10 border-l-2 border-emerald-500/70",
    cell &&
      !isTemplate &&
      rowKind === "mismatch" &&
      side === "left" &&
      "bg-red-500/10 border-l-2 border-red-500/70",
    cell &&
      !isTemplate &&
      rowKind === "mismatch" &&
      side === "right" &&
      "bg-emerald-500/10 border-l-2 border-emerald-500/70",
    cell &&
      !isTemplate &&
      rowKind === "exact" &&
      !highlightMatches &&
      "hover:bg-muted/40",
  );

  if (!cell) {
    return <div className={classes} />;
  }

  return (
    <div className={classes}>
      <pre className="m-0 w-full whitespace-pre-wrap break-words">
        {cell.tokens.map((token, idx) => (
          <span
            key={idx}
            className={cn(
              token.kind === "unchanged" && "",
              rowKind === "structural" &&
                token.kind !== "unchanged" &&
                highlightMatches &&
                "font-semibold bg-amber-500/30 text-amber-900 dark:bg-amber-500/40 dark:text-amber-50",
              rowKind !== "structural" &&
                token.kind === "removed" &&
                side === "left" &&
                "font-semibold bg-red-500/30 text-red-900 dark:bg-red-500/40 dark:text-red-50",
              rowKind !== "structural" &&
                token.kind === "added" &&
                side === "right" &&
                "font-semibold bg-emerald-500/30 text-emerald-900 dark:bg-emerald-500/40 dark:text-emerald-50",
            )}
          >
            {token.value}
          </span>
        ))}
      </pre>
    </div>
  );
}

function splitChangeLines(change: Change): string[] {
  const raw = change.value.split("\n");
  if (raw.length && raw[raw.length - 1] === "") {
    raw.pop();
  }
  return raw.map((line) => line.replace(/\r$/, ""));
}

function buildDiffRows(
  codeA: string,
  codeB: string,
  template: string,
  opts: {
    ignoreComments: boolean;
    ignoreVariableNames: boolean;
    functionSorting: boolean;
  },
): DiffRow[] {
  const templateLines = new Set(
    template
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0),
  );

  const lineDiff = diffLines(codeA, codeB);

  let aLine = 1;
  let bLine = 1;
  const rows: DiffRow[] = [];

  let i = 0;
  while (i < lineDiff.length) {
    const change = lineDiff[i];

    if (!change.added && !change.removed) {
      const lines = splitChangeLines(change);
      for (const text of lines) {
        const trimmed = text.trim();
        const isTemplate = trimmed.length > 0 && templateLines.has(trimmed);
        const tokens: DiffToken[] = text
          ? [{ value: text, kind: "unchanged" }]
          : [];

        const cell: DiffCell = {
          lineNumber: aLine,
          text,
          tokens,
          isTemplate,
        };

        rows.push({
          left: cell,
          right: {
            lineNumber: bLine,
            text,
            tokens: [...tokens],
            isTemplate,
          },
          kind: "exact",
        });

        aLine += 1;
        bLine += 1;
      }
      i += 1;
      continue;
    }

    if (change.removed && i + 1 < lineDiff.length && lineDiff[i + 1].added) {
      const removed = splitChangeLines(change);
      const added = splitChangeLines(lineDiff[i + 1]);

      const maxLen = Math.max(removed.length, added.length);
      for (let idx = 0; idx < maxLen; idx += 1) {
        const leftText = removed[idx] ?? "";
        const rightText = added[idx] ?? "";

        const hasLeft = idx < removed.length;
        const hasRight = idx < added.length;

        let kind: RowKind;
        if (hasLeft && hasRight) {
          if (leftText === rightText) {
            kind = "exact";
          } else {
            const normLeft = normalizeLine(leftText, opts);
            const normRight = normalizeLine(rightText, opts);
            if (normLeft && normLeft === normRight) {
              kind = "structural";
            } else {
              kind = "mismatch";
            }
          }
        } else if (hasLeft) {
          kind = "left-only";
        } else {
          kind = "right-only";
        }

        let leftTokens: DiffToken[] = [];
        let rightTokens: DiffToken[] = [];

        if (hasLeft && hasRight && (kind === "structural" || kind === "mismatch")) {
          const parts = diffWords(leftText, rightText);
          for (const part of parts) {
            if (part.removed) {
              leftTokens.push({ value: part.value, kind: "removed" });
            } else if (part.added) {
              rightTokens.push({ value: part.value, kind: "added" });
            } else {
              leftTokens.push({ value: part.value, kind: "unchanged" });
              rightTokens.push({ value: part.value, kind: "unchanged" });
            }
          }
        } else {
          if (hasLeft) {
            leftTokens = leftText
              ? [{ value: leftText, kind: "unchanged" }]
              : [];
          }
          if (hasRight) {
            rightTokens = rightText
              ? [{ value: rightText, kind: "unchanged" }]
              : [];
          }
        }

        const leftCell: DiffCell | null = hasLeft
          ? {
              lineNumber: aLine,
              text: leftText,
              tokens: leftTokens,
              isTemplate:
                leftText.trim().length > 0 &&
                templateLines.has(leftText.trim()),
            }
          : null;

        const rightCell: DiffCell | null = hasRight
          ? {
              lineNumber: bLine,
              text: rightText,
              tokens: rightTokens,
              isTemplate:
                rightText.trim().length > 0 &&
                templateLines.has(rightText.trim()),
            }
          : null;

        rows.push({
          left: leftCell,
          right: rightCell,
          kind,
        });

        if (hasLeft) {
          aLine += 1;
        }
        if (hasRight) {
          bLine += 1;
        }
      }

      i += 2;
      continue;
    }

    if (change.removed) {
      const removed = splitChangeLines(change);
      for (const text of removed) {
        const trimmed = text.trim();
        const tokens: DiffToken[] = text
          ? [{ value: text, kind: "removed" }]
          : [];
        const cell: DiffCell = {
          lineNumber: aLine,
          text,
          tokens,
          isTemplate: trimmed.length > 0 && templateLines.has(trimmed),
        };
        rows.push({
          left: cell,
          right: null,
          kind: "left-only",
        });
        aLine += 1;
      }
      i += 1;
      continue;
    }

    if (change.added) {
      const added = splitChangeLines(change);
      for (const text of added) {
        const trimmed = text.trim();
        const tokens: DiffToken[] = text
          ? [{ value: text, kind: "added" }]
          : [];
        const cell: DiffCell = {
          lineNumber: bLine,
          text,
          tokens,
          isTemplate: trimmed.length > 0 && templateLines.has(trimmed),
        };
        rows.push({
          left: null,
          right: cell,
          kind: "right-only",
        });
        bLine += 1;
      }
      i += 1;
      continue;
    }

    i += 1;
  }

  return rows;
}

function normalizeLine(
  line: string,
  opts: {
    ignoreComments: boolean;
    ignoreVariableNames: boolean;
    functionSorting: boolean;
  },
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
            "main",
          ].includes(match)
        ) {
          return match;
        }
        return "id";
      },
    );
  }

  if (opts.functionSorting) {
    // Reserved for future structural normalization.
  }

  return trimmed.replace(/\s+/g, " ");
}
