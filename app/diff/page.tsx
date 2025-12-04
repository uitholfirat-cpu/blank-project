"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { DiffViewer } from "@/components/diff/diff-viewer";
import { useReport } from "@/components/report-context";
import { professorTemplate } from "@/lib/professor-template";

function DiffPageContent() {
  const searchParams = useSearchParams();
  const pairId = searchParams.get("pairId");
  const { reportData } = useReport();

  if (!pairId) {
    return (
      <div className="space-y-4">
        <p className="text-sm font-medium text-foreground">No pair selected.</p>
        <p className="text-xs text-muted-foreground">
          Open this page from the plagiarism overview to inspect a specific pair.
        </p>
        <Link
          href="/plagiarism"
          className="inline-flex text-xs font-medium text-sky-400 underline-offset-4 hover:underline"
        >
          Back to plagiarism overview
        </Link>
      </div>
    );
  }

  if (!reportData || !reportData.plagiarismCases.length) {
    return (
      <div className="space-y-4">
        <p className="text-sm font-medium text-foreground">No data found.</p>
        <p className="text-xs text-muted-foreground">
          Upload a ZIP file and run the analysis before opening individual diffs.
        </p>
        <Link
          href="/"
          className="inline-flex text-xs font-medium text-sky-400 underline-offset-4 hover:underline"
        >
          Back to upload
        </Link>
      </div>
    );
  }

  const pair = reportData.plagiarismCases.find((p) => p.id === pairId);

  if (!pair) {
    return (
      <div className="space-y-4">
        <p className="text-sm font-medium text-foreground">Pair not found.</p>
        <p className="text-xs text-muted-foreground">
          The requested pair ID does not exist in the current report.
        </p>
        <Link
          href="/plagiarism"
          className="inline-flex text-xs font-medium text-sky-400 underline-offset-4 hover:underline"
        >
          Back to plagiarism overview
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DiffViewer pair={pair} template={professorTemplate} />
    </div>
  );
}

export default function DiffPage() {
  return (
    <Suspense fallback={<div className="text-xs text-muted-foreground">Loading diff…</div>}>
      <DiffPageContent />
    </Suspense>
  );
}