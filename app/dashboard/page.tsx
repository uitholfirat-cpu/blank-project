"use client";

import { useState } from "react";
import Link from "next/link";

import { StatsCards } from "@/components/dashboard/stats-cards";
import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { useReport } from "@/components/report-context";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const { reportData } = useReport();
  const [isLogOpen, setIsLogOpen] = useState(false);

  const hasData =
    !!reportData &&
    !!reportData.plagiarismCases &&
    reportData.plagiarismCases.length > 0;

  const processingErrors = reportData?.processingErrors ?? [];
  const hasProcessingErrors = processingErrors.length > 0;

  const handleDownload = (type: "csv" | "detailed" | "clusters") => {
    const files = reportData?.reportFiles;
    if (!files) return;

    const path = files[type];
    if (!path) return;

    const baseUrl =
      process.env.NODE_ENV === "development"
        ? "http://127.0.0.1:8000"
        : "";

    const url = path.startsWith("http") ? path : `${baseUrl}${path}`;
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Cohort overview
          </h1>
          <p className="text-xs text-muted-foreground">
            Monitor submissions across Q1–Q6, high-risk pairs, and overall
            similarity trends.
          </p>
        </div>

        {hasData && (
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-3">
            <span className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Export reports
            </span>
            <div className="inline-flex overflow-hidden rounded-md border border-border/80 bg-card/80 text-xs">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-none border-0 border-r border-border/70 px-3"
                onClick={() => handleDownload("csv")}
                disabled={!reportData?.reportFiles?.csv}
              >
                CSV
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-none border-0 border-r border-border/70 px-3"
                onClick={() => handleDownload("detailed")}
                disabled={!reportData?.reportFiles?.detailed}
              >
                Detailed TXT
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-none border-0 px-3"
                onClick={() => handleDownload("clusters")}
                disabled={!reportData?.reportFiles?.clusters}
              >
                Clusters CSV
              </Button>
            </div>
          </div>
        )}
      </header>

      {!hasData ? (
        <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border/80 bg-card/80 p-4 text-xs text-muted-foreground">
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
            to generate a report before viewing the dashboard.
          </p>
        </div>
      ) : (
        <>
          <StatsCards />
          <OverviewCharts />
          {hasProcessingErrors && (
            <section className="mt-2 rounded-xl border border-border/80 bg-card/80">
              <button
                type="button"
                className="flex w-full items-center justify-between px-4 py-2 text-xs font-medium text-foreground"
                onClick={() => setIsLogOpen((open) => !open)}
              >
                <span>Processing log</span>
                <span className="text-[0.7rem] text-muted-foreground">
                  {processingErrors.length} warning
                  {processingErrors.length === 1 ? "" : "s"} •{" "}
                  {isLogOpen ? "Hide" : "Show"}
                </span>
              </button>
              {isLogOpen && (
                <div className="border-t border-border/70 px-4 py-3 text-xs text-muted-foreground">
                  <ul className="space-y-1.5">
                    {processingErrors.map((message, index) => (
                      <li
                        key={`${index}-${message.slice(0, 32)}`}
                        className="flex gap-2"
                      >
                        <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
                        <span className="text-foreground/90">{message}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}