import type { Metadata } from "next";
import "./globals.css";

import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { SettingsProvider } from "@/components/settings/settings-context";

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
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <SettingsProvider>
            <div className="app-main">
              <Sidebar />
              <div className="app-content">
                <Topbar />
                <main className="flex-1 px-4 pb-8 pt-4 md:px-6 md:pt-6">
                  {children}
                </main>
              </div>
            </div>
          </SettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}