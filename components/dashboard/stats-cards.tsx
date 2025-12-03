"use client";

import { Users, ListChecks, AlertTriangle, Percent } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { useSettings } from "@/components/settings/settings-context";
import { useReport } from "@/components/report-context";

export function StatsCards() {
  const { settings } = useSettings();
  const { reportData } = useReport();

  if (!reportData) {
    return (
      <section className="rounded-xl border border-dashed border-border/80 bg-card/80 p-4 text-xs text-muted-foreground">
        <p className="text-sm font-medium text-foreground">No data found.</p>
        <p>Upload a ZIP file to view cohort statistics.</p>
      </section>
    );
  }

  const { dashboardStats } = reportData;

  const highRiskThreshold = settings.threshold ?? 85;
  const highRiskCasesAtThreshold = dashboardStats.highRiskCases;

  const cards = [
    {
      label: "Total students",
      value: dashboardStats.totalStudents.toLocaleString(),
      icon: Users,
      helper: "Across all lab sections"
    },
    {
      label: "Questions (Q1–Q6)",
      value: dashboardStats.totalQuestions.toString(),
      icon: ListChecks,
      helper: "Per-assignment core problems"
    },
    {
      label: "High-risk cases",
      value: highRiskCasesAtThreshold.toString(),
      icon: AlertTriangle,
      helper: `Similarity ≥ ${highRiskThreshold}%`
    },
    {
      label: "Average similarity",
      value: `${dashboardStats.averageSimilarity.toFixed(1)}%`,
      icon: Percent,
      helper: "Across flagged pairs"
    }
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.label}
            className="border-border/80 bg-card/90 shadow-soft-card"
          >
            <CardHeader className="mb-1 flex items-center justify-between gap-2">
              <CardTitle className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                {card.label}
              </CardTitle>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-500/10 text-sky-400 ring-1 ring-sky-500/30">
                <Icon className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tracking-tight">
                {card.value}
              </p>
              <CardDescription>{card.helper}</CardDescription>
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}