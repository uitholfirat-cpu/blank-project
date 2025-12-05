"use client";

import * as React from "react";

/**
 * Core domain types – kept in sync with:
 * - lib/mock-data.ts (frontend)
 * - api.py UploadResponse (backend)
 */

export type QuestionId = "Q1" | "Q2" | "Q3" | "Q4" | "Q5" | "Q6";

export type PlagiarismCase = {
  id: string;
  questionId: QuestionId;
  studentA: string;
  studentB: string;
  similarity: number;
  clusterId: string;
  codeA: string;
  codeB: string;
};

export type DashboardStats = {
  totalStudents: number;
  totalQuestions: number;
  highRiskCases: number;
  averageSimilarity: number;
};

export type GradeDistributionItem = {
  questionId: QuestionId;
  submissions: number;
  highRisk: number;
};

export type OriginalityStatItem = {
  label: string;
  value: number;
};

export type ReportFiles = {
  csv?: string;
  detailed?: string;
  clusters?: string;
};

export type ReportData = {
  plagiarismCases: PlagiarismCase[];
  dashboardStats: DashboardStats;
  gradeDistribution: GradeDistributionItem[];
  originalityStats: OriginalityStatItem[];
  processingErrors?: string[];
  reportFiles?: ReportFiles;
};

type ReportContextValue = {
  reportData: ReportData | null;
  setReportData: (data: ReportData | null) => void;
};

const ReportContext = React.createContext<ReportContextValue | undefined>(
  undefined
);

// Module-level bridge so callers can import and set data without using the hook
let externalSetReportData: ((data: ReportData | null) => void) | null = null;

export function ReportProvider({ children }: { children: React.ReactNode }) {
  const [reportData, setReportData] = React.useState<ReportData | null>(null);

  React.useEffect(() => {
    externalSetReportData = setReportData;
    return () => {
      externalSetReportData = null;
    };
  }, []);

  return (
    <ReportContext.Provider value={{ reportData, setReportData }}>
      {children}
    </ReportContext.Provider>
  );
}

export function useReport() {
  const ctx = React.useContext(ReportContext);
  if (!ctx) {
    throw new Error("useReport must be used within a ReportProvider");
  }
  return ctx;
}

/**
 * Convenience setter that can be imported directly.
 * Internally delegates to the active ReportProvider instance.
 */
export function setReportData(data: ReportData | null) {
  if (!externalSetReportData) {
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.warn(
        "setReportData was called before ReportProvider was mounted."
      );
    }
    return;
  }
  externalSetReportData(data);
}