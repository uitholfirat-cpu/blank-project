import type { Metadata } from "next";
import "./globals.css";

import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { SettingsProvider } from "@/components/settings/settings-context";
import { ReportProvider } from "@/components/report-context";

export const metadata: Metadata = {
  title: "MasterGrader – C Programming Plagiarism Engine",
  description:
    "AI-powered grading and plagiarism detection for C programming assignments."
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="h-screen overflow-hidden bg-background text-foreground antialiased">
        <ThemeProvider>
          <SettingsProvider>
            <ReportProvider>
              <div className="flex h-screen flex-col md:flex-row">
                <Sidebar />
                <div className="flex h-screen flex-1 flex-col overflow-hidden md:pl-64 lg:pl-72">
                  <Topbar />
                  <main className="flex-1 overflow-y-auto px-4 pb-8 pt-14 md:px-6 md:pt-20">
                    {children}
                  </main>
                </div>
              </div>
            </ReportProvider>
          </SettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}