import { StatsCards } from "@/components/dashboard/stats-cards";
import { OverviewCharts } from "@/components/dashboard/overview-charts";

export default function DashboardPage() {
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
      <StatsCards />
      <OverviewCharts />
    </div>
  );
}