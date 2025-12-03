"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell
} from "recharts";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { gradeDistribution, originalityStats } from "@/lib/mock-data";

const barColors = {
  submissions: "#38bdf8",
  highRisk: "#f97316"
};

const pieColors = {
  Original: "#22c55e",
  Suspicious: "#f97316"
};

export function OverviewCharts() {
  return (
    <section className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,_2fr)_minmax(0,_1.2fr)]">
      <Card className="border-border/80 bg-card/90">
        <CardHeader>
          <CardTitle className="text-sm font-semibold tracking-tight">
            Submissions per question
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={gradeDistribution}
              margin={{ top: 8, right: 16, left: -16, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148, 163, 184, 0.25)"
                vertical={false}
              />
              <XAxis
                dataKey="questionId"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tick={{ fontSize: 12, fill: "rgba(148, 163, 184, 0.9)" }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tick={{ fontSize: 11, fill: "rgba(148, 163, 184, 0.9)" }}
              />
              <Tooltip
                cursor={{ fill: "rgba(15, 23, 42, 0.25)" }}
                content={<CustomBarTooltip />}
              />
              <Bar
                dataKey="submissions"
                name="Submissions"
                stackId="a"
                fill={barColors.submissions}
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="highRisk"
                name="High-risk"
                stackId="a"
                fill={barColors.highRisk}
                radius={[0, 0, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="border-border/80 bg-card/90">
        <CardHeader>
          <CardTitle className="text-sm font-semibold tracking-tight">
            Original vs suspicious
          </CardTitle>
        </CardHeader>
        <CardContent className="flex h-[260px] items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={originalityStats}
                dataKey="value"
                nameKey="label"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                stroke="rgba(15, 23, 42, 0.9)"
                strokeWidth={2}
              >
                {originalityStats.map((entry) => (
                  <Cell
                    key={entry.label}
                    fill={pieColors[entry.label as keyof typeof pieColors]}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </section>
  );
}

function CustomBarTooltip({
  active,
  payload,
  label
}: {
  active?: boolean;
  payload?: any[];
  label?: string;
}) {
  if (!active || !payload || !payload.length) return null;

  const submissions = payload.find((p) => p.dataKey === "submissions")?.value;
  const highRisk = payload.find((p) => p.dataKey === "highRisk")?.value;

  return (
    <div className="rounded-md border border-border/80 bg-background/95 px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 font-medium text-foreground/90">
        Question {label}
      </div>
      <div className="space-y-0.5 text-muted-foreground">
        <div className="flex items-center justify-between gap-4">
          <span className="inline-flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: barColors.submissions }}
            />
            Submissions
          </span>
          <span className="font-medium text-foreground/90">
            {submissions ?? 0}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="inline-flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: barColors.highRisk }}
            />
            High-risk pairs
          </span>
          <span className="font-medium text-foreground/90">
            {highRisk ?? 0}
          </span>
        </div>
      </div>
    </div>
  );
}

function CustomPieTooltip({
  active,
  payload
}: {
  active?: boolean;
  payload?: any[];
}) {
  if (!active || !payload || !payload.length) return null;

  const item = payload[0];
  const value = item.value;
  const label = item.name;

  return (
    <div className="rounded-md border border-border/80 bg-background/95 px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 font-medium text-foreground/90">{label}</div>
      <div className="flex items-center justify-between gap-4 text-muted-foreground">
        <span>Submissions</span>
        <span className="font-medium text-foreground/90">{value}%</span>
      </div>
    </div>
  );
}