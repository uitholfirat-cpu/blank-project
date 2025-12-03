"use client";

import Link from "next/link";

import { StatsCards } from "@/components/dashboard/stats-cards";
import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { useReport } from "@/components/report-context";

export default function DashboardPage() {
  const { reportData } = useReport();

  const hasData =
    reportData &&
    reportData.plagiarismCases &&
    reportData.plagiarismCases.length > 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold tracking-tight">
          Cohort overview
        </h1>
        <p className="text-xs text-muted-foreground">
          Monitor submissions across Q1–Q6, high-risk pairs, and overall
          similarity trends.
        </p>
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
        </>
      )}
    </div>
  );
}