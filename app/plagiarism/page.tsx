"use client";

import Link from "next/link";

import { PlagiarismTable } from "@/components/plagiarism/plagiarism-table";
import { PlagiarismGraph } from "@/components/plagiarism/plagiarism-graph";
import { useReport } from "@/components/report-context";

export default function PlagiarismPage() {
  const { reportData } = useReport();
  const cases = reportData?.plagiarismCases ?? [];

  if (!cases.length) {
    return (
      <div className="space-y-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold tracking-tight">
            Plagiarism engine
          </h1>
          <p className="text-xs text-muted-foreground">
            Investigate suspicious pairs, then pivot into a network view of
            suspected cheating rings.
          </p>
        </header>
        <div className="rounded-xl border border-dashed border-border/80 bg-card/80 p-4 text-xs text-muted-foreground">
          <p className="text-sm font-medium text-foreground">
            No data found.
          </p>
          <p>
            Upload a ZIP file on the{" "}
            <Link
              href="/"
              className="font-medium text-sky-400 underline-offset-4 hover:underline"
            >
              upload page
            </Link>{" "}
            to see suspicious pairs and cluster graphs.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold tracking-tight">
          Plagiarism engine
        </h1>
        <p className="text-xs text-muted-foreground">
          Investigate suspicious pairs, then pivot into a network view of
          suspected cheating rings.
        </p>
      </header>
      <PlagiarismTable cases={cases} />
      <PlagiarismGraph cases={cases} />
    </div>
  );
}