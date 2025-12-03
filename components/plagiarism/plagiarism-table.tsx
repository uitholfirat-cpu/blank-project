"use client";

import { useMemo, useState } from "react";
import { ArrowDownWideNarrow, ArrowUpWideNarrow, Search } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { useSettings } from "@/components/settings/settings-context";
import type { PlagiarismCase, QuestionId } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type SortKey = "similarity" | "questionId" | "student";

type PlagiarismTableProps = {
  cases: PlagiarismCase[];
};

const questionLabels: Record<QuestionId, string> = {
  Q1: "Q1 – Loops & sums",
  Q2: "Q2 – Recursion",
  Q3: "Q3 – Primes",
  Q4: "Q4 – Arrays",
  Q5: "Q5 – Branching",
  Q6: "Q6 – GCD"
};

export function PlagiarismTable({ cases }: PlagiarismTableProps) {
  const router = useRouter();
  const { settings } = useSettings();
  const [sortKey, setSortKey] = useState<SortKey>("similarity");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [questionFilter, setQuestionFilter] = useState<QuestionId | "all">(
    "all"
  );
  const [search, setSearch] = useState("");

  const threshold = settings.threshold ?? 80;

  const filteredAndSorted = useMemo(() => {
    let result = [...cases];

    if (questionFilter !== "all") {
      result = result.filter((c) => c.questionId === questionFilter);
    }

    if (search.trim()) {
      const query = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.studentA.toLowerCase().includes(query) ||
          c.studentB.toLowerCase().includes(query)
      );
    }

    result.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortKey === "similarity") {
        return (a.similarity - b.similarity) * dir;
      }
      if (sortKey === "questionId") {
        return a.questionId.localeCompare(b.questionId) * dir;
      }
      const nameA = `${a.studentA} ${a.studentB}`;
      const nameB = `${b.studentA} ${b.studentB}`;
      return nameA.localeCompare(nameB) * dir;
    });

    return result;
  }, [cases, questionFilter, search, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "similarity" ? "desc" : "asc");
    }
  };

  const getSimilarityBadgeVariant = (similarity: number) => {
    if (similarity >= threshold) return "danger" as const;
    if (similarity >= threshold - 15) return "warning" as const;
    if (similarity >= threshold - 30) return "success" as const;
    return "outline" as const;
  };

  const getSimilarityLabel = (similarity: number) => {
    if (similarity >= threshold) return "High risk";
    if (similarity >= threshold - 15) return "Suspicious";
    if (similarity >= threshold - 30) return "Borderline";
    return "Low";
  };

  return (
    <section className="space-y-4">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Suspicious pairs
          </h2>
          <p className="text-xs text-muted-foreground">
            Sorted by similarity. Click a row to open a side-by-side code diff.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative w-full sm:w-60">
            <Search className="pointer-events-none absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search by student..."
              className="pl-7 text-xs"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="mt-1 h-9 rounded-md border border-input bg-background/90 px-2 text-xs font-medium text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:mt-0"
            value={questionFilter}
            onChange={(e) =>
              setQuestionFilter(
                e.target.value === "all"
                  ? "all"
                  : (e.target.value as QuestionId)
              )
            }
          >
            <option value="all">All questions</option>
            {(["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"] as QuestionId[]).map(
              (id) => (
                <option key={id} value={id}>
                  {questionLabels[id]}
                </option>
              )
            )}
          </select>
        </div>
      </header>

      <div className="overflow-hidden rounded-xl border border-border/80 bg-card/90 shadow-soft-card">
        <div className="max-h-[420px] overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-xs font-medium uppercase tracking-[0.16em]"
                    onClick={() => toggleSort("questionId")}
                  >
                    Question
                    <SortIcon active={sortKey === "questionId"} dir={sortDir} />
                  </button>
                </TableHead>
                <TableHead>Student A</TableHead>
                <TableHead>Student B</TableHead>
                <TableHead className="w-[160px] text-right">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-xs font-medium uppercase tracking-[0.16em]"
                    onClick={() => toggleSort("similarity")}
                  >
                    Similarity
                    <SortIcon active={sortKey === "similarity"} dir={sortDir} />
                  </button>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSorted.map((pair) => (
                <TableRow
                  key={pair.id}
                  className="cursor-pointer bg-background/60 text-sm transition-colors hover:bg-accent/40"
                  onClick={() => router.push(`/diff/${pair.id}`)}
                >
                  <TableCell className="text-xs font-semibold">
                    <span className="inline-flex rounded-full bg-muted px-2 py-0.5 text-[0.7rem] font-medium">
                      {pair.questionId}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs">
                    <div className="flex flex-col">
                      <span className="font-medium">{pair.studentA}</span>
                      <span className="text-[0.68rem] text-muted-foreground">
                        Submission A
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">
                    <div className="flex flex-col">
                      <span className="font-medium">{pair.studentB}</span>
                      <span className="text-[0.68rem] text-muted-foreground">
                        Submission B
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-xs">
                    <div className="flex flex-col items-end gap-1">
                      <Badge
                        variant={getSimilarityBadgeVariant(pair.similarity)}
                        className={cn(
                          "min-w-[96px] justify-end text-[0.7rem]",
                          pair.similarity >= threshold &&
                            "animate-[pulse_2s_ease-in-out_infinite]"
                        )}
                      >
                        <span className="tabular-nums">
                          {pair.similarity.toFixed(0)}%
                        </span>
                        <span className="ml-1.5 text-[0.65rem] tracking-[0.16em] uppercase">
                          {getSimilarityLabel(pair.similarity)}
                        </span>
                      </Badge>
                      <span className="text-[0.65rem] text-muted-foreground">
                        Cluster: {pair.clusterId}
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {filteredAndSorted.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="py-8 text-center text-xs text-muted-foreground"
                  >
                    No suspicious pairs match the current filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        <footer className="flex items-center justify-between border-t border-border/80 px-4 py-2 text-[0.7rem] text-muted-foreground">
          <span>
            Threshold: <span className="font-semibold">{threshold}%</span> &mdash>{" "}
            adjusted in{" "}
            <span className="underline underline-offset-2">Settings</span>.
          </span>
          <span className="hidden sm:inline">
            Click a row to open the diff viewer.
          </span>
        </footer>
      </div>
    </section>
  );
}

function SortIcon({
  active,
  dir
}: {
  active: boolean;
  dir: "asc" | "desc";
}) {
  const Icon = dir === "asc" ? ArrowUpWideNarrow : ArrowDownWideNarrow;
  return (
    <Icon
      className={cn(
        "h-3 w-3 text-muted-foreground transition-colors",
        active && "text-foreground"
      )}
    />
  );
}